"""
This module reads .csv files from our ingestion bucket,
and converts them to a pandas data frame.
This module contains four functions:
fact_sales_order_data_frame - reads the CSV file and
returns a DataFrame.
Errors:
    TypeError - if input is not a string
    ValueError - Catching the specific ValueError
    ClientError - Catch the error if the table name is non-existent
    FileNotFoundError - if the file was not found
    Exception - for general errors
"""
import boto3
import pandas as pd
import io
from botocore.exceptions import ClientError
import logging
from pprint import pprint

logger = logging.getLogger('MyLogger')
logger.setLevel(logging.INFO)


def fact_sales_order_data_frame(sales_order_table):
    """
    The function fact_sales_order_data_frame reads a .csv file from our
    ingestion bucket and manipulate columns name with specific datatype
    and return a nice data frame for sales table and for date table
    Arguments:
    sales_order_table (string) - represents the name of a table
    in our database.
    Output:
    data_frame (DataFrame) - outputs the read .csv file as a pandas
    DataFrame for use with other functions
    date_df (DataFrame) - is a DataFrame with all date format
    obtained from the sales order table
    Errors:
    TypeError - if input is not a string
    ValueError - Catching the specific ValueError
    ClientError - Catch the error if the table name is non-existent
    FileNotFoundError - if the file was not found
    Exception - for general errors

    """

    try:
        # Check for empty input name
        if len(sales_order_table) == 0:
            raise ValueError("No input name")

        # Define file name
        file_name = sales_order_table + ".csv"

        # Connect to S3 client
        s3 = boto3.client('s3')

        file = s3.get_object(
            Bucket='ingested-data-vox-indicium', Key=file_name)

        # Define the column names
        # col_names = ['sales_order_id',
        #              'created_at',
        #              'last_updated',
        #              'design_id',
        #              'staff_id',
        #              'counterparty_id',
        #              'units_sold',
        #              'unit_price',
        #              'currency_id',
        #              'agreed_delivery_date',
        #              'agreed_payment_date',
        #              'agreed_delivery_location_id']

        # Read the CSV file using the column names
        data_frame = pd.read_csv(io.StringIO(
            file['Body'].read().decode('utf-8')))

        # Extract the date and time parts for both
        # 'created_at' and 'last_updated' columns
        data_frame['created_date'] = pd.DataFrame(
            data={'created_at':
                  [x.split(' ')[0] for x in list(data_frame['created_at'])]})
        data_frame['created_time'] = pd.DataFrame(
            data={'created_at':
                  [x.split(' ')[1] for x in list(data_frame['created_at'])]})
        data_frame['last_updated_date'] = pd.DataFrame(
            data={'last_updated':
                  [x.split(' ')[0] for x in list(data_frame['last_updated'])]})
        data_frame['last_updated_time'] = pd.DataFrame(
            data={'last_updated':
                  [x.split(' ')[1] for x in list(data_frame['last_updated'])]})

        # Drop the original 'created_at' and 'last_updated' columns
        data_frame = data_frame.drop(columns=['created_at', 'last_updated'])

        # Change name of staff_id to sales_staff_id
        data_frame.rename(columns={'staff_id': 'sales_staff_id'}, inplace=True)

        # Create a new column to be used like primary key
        data_frame['sales_record_id'] = range(1, len(data_frame)+1)

        # Move this column to the front of table
        p_key = data_frame['sales_record_id']
        data_frame.drop(labels=['sales_record_id'], axis=1, inplace=True)
        data_frame.insert(0, 'sales_record_id', p_key)

        # Create date DataFrame
        # unique_dates = set(data_frame['created_date'].tolist() +
        # data_frame['last_updated_date'].tolist() +
        # data_frame['agreed_delivery_date'].tolist() +
        # data_frame['agreed_payment_date'].tolist())
        # date_rows = []
        # for unique_date in unique_dates:
        #     date_info = pd.to_datetime(unique_date)
        #     row = {
        #         'date_id': unique_date,
        #         'year': date_info.year,
        #         'month': date_info.month,
        #         'day': date_info.day,
        #         'day_of_week': date_info.dayofweek,
        #         'day_name': date_info.strftime('%A'),
        #         'month_name': date_info.strftime('%B'),
        #         'quarter': (date_info.month-1)//3 + 1
        #     }
        #     date_rows.append(row)

        # date_df = pd.DataFrame(date_rows,
        # columns=['date_id', 'year', 'month', 'day', 'day_of_week',
        # 'day_name', 'month_name', 'quarter'])

        # Set the column data types for sales_order_table
        data_frame = data_frame.astype({
            'sales_record_id': 'int',
            'sales_order_id': 'int',
            'created_date': 'str',
            'created_time': 'str',
            'last_updated_date': 'str',
            'last_updated_time': 'str',
            'design_id': 'int',
            'sales_staff_id': 'int',
            'counterparty_id': 'int',
            'units_sold': 'int',
            'unit_price': 'float',
            'currency_id': 'int',
            'agreed_delivery_date': 'str',
            'agreed_payment_date': 'str',
            'agreed_delivery_location_id': 'int'
        })

        # Set the column data types for date table
        # date_df = date_df.astype({
        #     'date_id': 'str',
        #     'year': 'int',
        #     'month': 'int',
        #     'day': 'int',
        #     'day_of_week': 'int',
        #     'day_name': 'str',
        #     'month_name': 'str',
        #     'quarter': 'int'
        # })

        # Return the final DataFrame
        # date_df.to_csv('date.csv', index=False)
        # data_frame.to_csv('salesss.csv', index=False)
        # print(data_frame, date_df)

        data_frame = data_frame.reindex(columns=[
            'sales_record_id',
            'sales_order_id',
            'created_date',
            'created_time',
            'last_updated_date',
            'last_updated_time',
            'sales_staff_id',
            'counterparty_id',
            'units_sold',
            'unit_price',
            'currency_id',
            'design_id',
            'agreed_payment_date',
            'agreed_delivery_date',
            'agreed_delivery_location_id'])

        return data_frame

    except ValueError as e:
        # Catching the specific ValueError before the generic Exception
        raise e

    except ClientError as e:
        # Catch the error if the table name is non-existent
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError(f"The file {sales_order_table} does not exist")
        else:
            raise e

    except TypeError as e:
        # catches the error if the user tap an incorrect input
        raise e

    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_name} does not exist locally")

    except Exception as e:
        # Generic exception to catch any other errors
        raise Exception(f"An unexpected error occurred: {e}")


def create_and_push_parquet(data_frame, file_name):
    '''
    Convert the DataFrames to a parquet format and
    push it to the processed s3 bucket.
    Arguments:
    data_frame - represent the DataFrame from of sales
    table the function fact_sales_order_data_frame.
    date_df - represent the DataFrame of date table from
    the function fact_sales_order_data_frame
    sales_order_table (string) - represents the name of a
    table in our database.
    dim_date (string) - represents the name of a table in
    our database
    '''
    try:
        # Save DataFrame to a parquet file in memory
        parquet_buffer = io.BytesIO()
    
        orig_close = parquet_buffer.close
        parquet_buffer.close = lambda: None

        data_frame.to_parquet(parquet_buffer, engine='fastparquet', index=False)
        parquet_buffer.close = orig_close

        pprint(parquet_buffer)
        # Connect to S3 client
        s3 = boto3.client('s3')

        # Send the parquet files to processed-data-vox-indicium s3 bucket
        s3.put_object(Bucket='processed-data-vox-indicium',
                      Key=f'{file_name}.parquet',
                      Body=parquet_buffer.getvalue())

        # Print a confirmation message
        logger.info(
            f"Parquet file '{file_name}.parquet' created in S3 bucket.")
        return f"'{file_name}.parquet' created and stored in S3 bucket."

    except Exception as e:
        # Generic exception for unexpected errors during conversion
        raise Exception(f"An error occurred while converting to parquet: {e}")


def main():
    '''
    Runs both functions to create and transfer the final parquet file.
    '''
    try:
        # Table name for the tables used in the dataframe
        sales_order_table = 'sales_order'

        # The name of the parquet file
        fact_sales_order = "fact_sales_order"

        # Call the fact_sales_order_data_frame function
        sales_df = fact_sales_order_data_frame(sales_order_table)

        # Call the create_and_push_parquet function
        create_and_push_parquet(sales_df, fact_sales_order)

    # Generic exception for unexpected errors during the function
    except Exception as e:
        print(f"An error occurred in the main function: {e}")
