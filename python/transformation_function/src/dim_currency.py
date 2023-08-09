"""
This module reads .csv files from our ingestion bucket, and converts
them to a pandas data frame.
This module contains three functions:
dim_currency_data_frame - reads the CSV file and returns a DataFrame.
create_parquet - converts the DataFrame to a parquet file.
push_parquet_file - copies the parquet file from one Amazon S3 bucket to
another and then deletes the original.
main - runs both functions to create and transfer the final parquet file.
FYI: ccy-1.3.1-py3-none-any.whl
"""
import boto3
import pandas as pd
import io
import ccy
from botocore.exceptions import ClientError


def dim_currency_data_frame(table_name):
    """
    The function dim_currency_data_frame reads a .csv file from our ingestion
    bucket and manipulates column names with specific data types, then
    returns a nice DataFrame.
    Arguments:
    table_name (string) - represents the name of a table in our database.
    Output:
    resulting_df (DataFrame) - outputs the read .csv file as a pandas
    DataFrame for use with other functions
    Errors:
    TypeError - if input is not a string
    ValueError - if input is not a valid table name
    """

    try:
        # Check for empty input name
        if len(table_name) == 0:
            raise ValueError("No input name")

        # Define file name
        file_name = table_name + ".csv"

        # Connect to S3 client
        s3 = boto3.client('s3')

        file = s3.get_object(
            Bucket='ingested-data-vox-indicium', Key=file_name)

        # Read the CSV file using the column names
        data_frame = pd.read_csv(io.StringIO(
            file['Body'].read().decode('utf-8')))

        # Drop the original datetime columns
        data_frame = data_frame.drop(columns=['created_at', 'last_updated'])

        # Populate dataframe with currency name
        currency_code_list = list(data_frame['currency_code'])

        currency_name_list = [ccy.currency(currency_code).__dict__[
            'name'] for currency_code in currency_code_list]
        data_frame = data_frame.assign(currency_name=currency_name_list)

        # Set the column data types
        data_frame = data_frame.astype({
            "currency_id": "int",
            "currency_code": "str",
            "currency_name": "str"
        })

        # Return the final DataFrame
        return data_frame

    except ValueError as e:
        # Catching the specific ValueError before the generic Exception
        raise e
    except ClientError as e:
        # Catch the error if the table name is non-existent
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError(f"The file {table_name} does not exist")
        else:
            raise e
    except TypeError as e:
        # Catches the error if the user taps an incorrect input
        raise e
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_name} does not exist")
    except Exception as e:
        # Generic exception to catch any other errors
        raise Exception(f"An unexpected error occurred: {e}")
