"""
This module reads .csv files from our ingestion bucket,
and converts them to a pandas data frame.
This module contains three functions:
dim_counterparty_data_frame - reads the CSV files and returns a DataFrame.
create_and_push_parquet - converts the DataFrame to a parquet file and
push the parquet file in the process data bucket
main - runs all functions to create the final parquet file.
"""

import boto3
import pandas as pd
import io
from botocore.exceptions import ClientError


def dim_counterparty_data_frame(counterparty_table, address_table):
    """
    The function dim_counterparty_data_frame reads the .csv files from our
    ingestion bucket and manipulate columns name with specific datatype and
    return a nice data frame.
    Arguments:
    counterparty_table (string) - represents the name of counterparty table
    from ingestion bucket.
    address_table (string) - represents the name of address table from
    ingestion bucket.
    Output:
    data_frame (DataFrame) - outputs the read .csv files as a pandas
    DataFrame with information from the both tables
    Errors:
    TypeError - if input is not a string
    ValueError - Catching the specific ValueError
    ClientError - Catch the error if the table name is non-existent
    FileNotFoundError - if the file was not found
    Exception - for general errors

    """

    try:
        # Check for empty input name
        if len(counterparty_table) == 0 or len(address_table) == 0:
            raise ValueError("No input name")

        # Define file name
        counterparty_name = counterparty_table + ".csv"
        address_name = address_table + ".csv"

        # Connect to S3 client
        s3 = boto3.client('s3')

        # Get the objects from ingested-data-vox-indicium S3 bucket
        counterparty_file = s3.get_object(
            Bucket='ingested-data-vox-indicium', Key=counterparty_name)
        address_file = s3.get_object(
            Bucket='ingested-data-vox-indicium', Key=address_name)

        # Read the CSV file using the column names
        counterparty_df = pd.read_csv(io.StringIO(
            counterparty_file['Body'].read().decode('utf-8')))
        address_df = pd.read_csv(io.StringIO(
            address_file['Body'].read().decode('utf-8')))

        # Merge counterparty_df and address_df DataFrames
        # on matching 'legal_address_id' and 'address_id',
        # retaining distinct suffixes for overlapping columns
        merged_df = pd.merge(counterparty_df, address_df,
                             left_on='legal_address_id',
                             right_on='address_id', suffixes=('', '_address'))

        # Rename and reorder the columns
        data_frame = merged_df.rename(columns={
            'counterparty_legal_name': 'counterparty_legal_name',
            'address_line_1': 'counterparty_legal_address_line_1',
            'address_line_2': 'counterparty_legal_address_line2',
            'district': 'counterparty_legal_district',
            'city': 'counterparty_legal_city',
            'postal_code': 'counterparty_legal_postal_code',
            'country': 'counterparty_legal_country',
            'phone': 'counterparty_legal_phone_number'
        })

        selected_columns = [
            'counterparty_id', 'counterparty_legal_name',
            'counterparty_legal_address_line_1',
            'counterparty_legal_address_line2',
            'counterparty_legal_district', 'counterparty_legal_city',
            'counterparty_legal_postal_code', 'counterparty_legal_country',
            'counterparty_legal_phone_number'
        ]

        # Create the date frame with the desired columns
        data_frame = data_frame[selected_columns]

        # Set the column data types for the final table
        data_frame = data_frame.astype({
            "counterparty_id": "int",
            "counterparty_legal_name": "str",
            "counterparty_legal_address_line_1": "str",
            "counterparty_legal_address_line2": "str",
            "counterparty_legal_district": "str",
            "counterparty_legal_city": "str",
            "counterparty_legal_postal_code": "str",
            "counterparty_legal_country": "str",
            "counterparty_legal_phone_number": "str"
        })
        # Sorted the date frame
        data_frame.sort_values(by='counterparty_id', inplace=True)

        data_frame = data_frame.replace('nan', '')
        # Return the final DataFrame
        return data_frame

    except ValueError as e:
        # Catching the specific ValueError before the generic Exception
        raise e

    except ClientError as e:
        # Catch the error if the table name is non-existent
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError(
                f"{counterparty_table} or {address_table} do not exist")
        else:
            raise e

    except TypeError as e:
        # Catches the error if the user tap an incorrect input
        raise e

    except FileNotFoundError:
        raise FileNotFoundError(
            f"The file {counterparty_table} or {address_table} does not exist")

    except Exception as e:
        # Generic exception to catch any other errors
        raise Exception(f"An unexpected error occurred: {e}")
