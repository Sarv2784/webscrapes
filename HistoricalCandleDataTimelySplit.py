import http.client
import json

import pandas as pd
from datetime import datetime, timedelta
import pytz
from pandas import json_normalize
import argparse

base_url = 'api.coinbase.com'
scrape_path = "/api/v3/brokerage/market/products/BTC-USD/candles?start={0}&end={1}&granularity={2}&limit={3}"


def parse_args():
    parser = argparse.ArgumentParser(description="Greet the user with their name and age.")

    # Add arguments
    parser.add_argument("start_date", type=str, help="start date in format 'MM/DD/YYYY")
    parser.add_argument("end_date", type=str, help="end_date in format 'MM/DD/YYYY")
    parser.add_argument("start_time", type=str, help="start time in format 'HH:mm:ss'")
    parser.add_argument("end_date", type=str, help="end time in format 'HH:mm:ss'")
    parser.add_argument("time_interval", type=str, choices=['ONE_HOUR', 'ONE_DAY'], help="time interval")
    parser.add_argument("no_of_items", type=int, help="number of items")

    # Parse the arguments
    return parser.parse_args()


def convert_time_est_to_unix(est_time: datetime):
    est = pytz.timezone('US/Eastern')
    localized_time = est.localize(est_time)
    utc_time = localized_time.astimezone(pytz.utc)
    return int(utc_time.timestamp())


def get_bitcoin_hourly_prices(est_start_date: str, est_end_date: str, start_time: str, end_time: str,
                              granularity='ONE_HOUR', limit=12):
    data_list = pd.DataFrame(columns=["start", "low", "high", "open", "close", "volume"])
    start_date = datetime.strptime(est_start_date, '%m/%d/%Y')
    end_date = datetime.strptime(est_end_date, '%m/%d/%Y')
    start_time_part = datetime.strptime(start_time, '%H:%M:%S').time()
    end_time_part = datetime.strptime(end_time, '%H:%M:%S').time()
    current_date = start_date
    payload = ''
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        conn = http.client.HTTPSConnection(base_url)
        while end_date <= current_date:
            unix_start_time = convert_time_est_to_unix(datetime.combine(current_date, start_time_part))
            unix_end_time = convert_time_est_to_unix(datetime.combine(current_date, end_time_part))
            formatted_api = scrape_path.format(unix_start_time, unix_end_time, granularity, limit)
            conn.request("GET", formatted_api, payload, headers)
            res = conn.getresponse()
            json_string = res.read().decode('utf-8')
            json_data = json.loads(json_string)
            candles_date = json_data['candles']
            data_list = pd.concat([data_list, json_normalize(candles_date)], ignore_index=True)

            current_date -= timedelta(days=1)
    except Exception as err:
        print(str(err))

    save_data(data_list)


def save_data(data_list):
    df = pd.DataFrame(data_list)
    df['start'] = pd.to_datetime(df['start'], unit='s', utc=True)
    df['start'] = df['start'].dt.tz_convert('US/Eastern')
    df['day_name'] = df['start'].dt.day_name()
    df['open'] = pd.to_numeric(df['open'])
    df['close'] = pd.to_numeric(df['close'])
    df['price_change'] = df['open'] - df['close']
    df['hour'] = df['start'].dt.hour

    for hour, group in df.groupby('hour'):
        filename = f"/Users/Victoria/PycharmProjects/BTCData/hour_{hour:02d}.csv"
        group.to_csv(filename, index=False)
        print(f"Saved file: {filename}")


if __name__ == '__main__':
    args  = parse_args()
    get_bitcoin_hourly_prices(args.start_date, args.end_date,
                              args.start_time, args.end_time, args.time_interval, args.no_of_items)
