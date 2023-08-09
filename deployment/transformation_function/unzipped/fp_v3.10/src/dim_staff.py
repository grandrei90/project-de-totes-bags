"""
This module reads .csv files from our ingestion bucket, and converts
them to a pandas data frame.
This module contains three functions:
dim_staff_data_frame - reads the CSV files and returns a DataFrame.
create_and_push_parquet - converts the DataFrame to a parquet file and
push the parquet file in the process data bucket
main - runs all functions to create the final parquet file.
"""

import boto3
import pandas as pd
import io
from botocore.exceptions import ClientError


def dim_staff_data_frame(staff_table, department_table):
    """
    The function dim_staff_data_frame reads the .csv files from our
    ingestion bucket and manipulate columns name with specific datatype
    and return a nice data frame.
    Arguments:
    staff_table (string) - represents the name of staff table from
    ingestion bucket.
    department_table (string) - represents the name of department
    table from ingestion bucket.
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
        if len(staff_table) == 0 or len(department_table) == 0:
            raise ValueError("No input name")

        # Define file name
        staff_name = staff_table + ".csv"
        department_name = department_table + ".csv"

        # Connect to S3 client
        s3 = boto3.client('s3')

        # Get the objects from ingestion-data-vox-indicium S3 bucket
        staff_file = s3.get_object(
            Bucket='ingestion-data-vox-indicium', Key=staff_name)
        department_file = s3.get_object(
            Bucket='ingestion-data-vox-indicium', Key=department_name)

        # Define the column names
        # staff_col_names = ['staff_id',
        #                    'first_name',
        #                    'last_name',
        #                    'department_id',
        #                    'email_address',
        #                    'created_at timestamp',
        #                    'last_updated']

        # department_col_names = ['department_id',
        #                         'department_name',
        #                         'location',
        #                         'manager',
        #                         'created_at',
        #                         'last_updated']

        # Read the CSV files using the column names
        staff_df = pd.read_csv(io.StringIO(
            staff_file['Body'].read().decode('utf-8')))
        department_df = pd.read_csv(io.StringIO(
            department_file['Body'].read().decode('utf-8')))

        # Merge staff_df and department_df DataFrames on matching
        # 'department_id' and 'department_id',
        # retaining distinct suffixes for overlapping columns
        merged_df = pd.merge(staff_df, department_df,
                             left_on='department_id',
                             right_on='department_id',
                             suffixes=('', '_department'))

        selected_columns = [
            'staff_id', 'first_name', 'last_name',
            'department_name', 'location', 'email_address'
        ]

        # Create the date frame with the desired columns
        data_frame = merged_df[selected_columns]

        # Set the column data types for the final table
        data_frame = data_frame.astype({
            'staff_id': 'int',
            'first_name': 'str',
            'last_name': 'str',
            'department_name': 'str',
            'location': 'str',
            'email_address': 'str'
        })

        # Sorted the date frame
        data_frame.sort_values(by='staff_id', inplace=True)

        # Return the final DataFrame
        return data_frame

    except ValueError as e:
        # Catching the specific ValueError before the generic Exception
        raise e

    except ClientError as e:
        # Catch the error if the table name is non-existent
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError(
                f"{staff_table} or {department_table} do not exist")
        else:
            raise e

    except TypeError as e:
        # Catches the error if the user tap an incorrect input
        raise e

    except FileNotFoundError:
        raise FileNotFoundError(
            f"The file {staff_table} or {department_table} does not exist")

    except Exception as e:
        # Generic exception to catch any other errors
        raise Exception(f"An unexpected error occurred: {e}")


