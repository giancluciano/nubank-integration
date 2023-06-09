from pynubank import Nubank
import os
from dotenv import load_dotenv
from datetime import datetime, date
from pandas import date_range, read_excel
from typing import List
from models import Transfer
from pony.orm import db_session, select, desc

date_format = '%Y-%m-%d'

class NubankIntegration:
    ''' https://github.com/andreroggeri/pynubank '''

    def __init__(self) -> None:
        load_dotenv()
        self.nu = Nubank()
        self.nu.authenticate_with_cert(os.getenv("USERNAME"), os.getenv("PASSWORD"), 'cert.p12')
        self._transfers = []
        self._bills = []
        self._investiment = {}

    def get_account_balance(self):
        return self.nu.get_account_balance()

    def get_account_statements(self):
        if self._transfers:
            return self._transfers
        transfers = []
        cursor = None
        has_next_page = True
        while has_next_page:
            account_statements = self.nu.get_account_statements_paginated(cursor)
            has_next_page = account_statements['pageInfo']['hasNextPage']
            cursor = account_statements['edges'][-1]['cursor']
            for transaction in account_statements['edges']:
                _, created = Transfer.get_or_create(transaction['node'])
                if not created:
                    has_next_page = False
                    break
        with db_session:
            transfers_query = select(t for t in Transfer).order_by(lambda t: desc(t.date))
            transfers.extend([transfer for transfer in transfers_query])
        self._transfers = transfers
        return transfers
    
    def get_month_account_statements(self,  year_month:date):
        if not self._transfers:
            self.get_account_statements()
        year_month = year_month.replace(day=1)
        month_transfers = []
        for transfer in self._transfers:
            if year_month and transfer.date.year > year_month.year or (transfer.date.year == year_month.year and transfer.date.month > year_month.month):
                continue
            if year_month and transfer.date < year_month:
                break
            month_transfers.append(transfer)
        return month_transfers

    def get_month_bill(self, year_month:date):
        # if needed we can have bill_details = nu.get_bill_details(bills[0])
        year_month = year_month.replace(day=1)
        self._bills = self.nu.get_bills() if not self._bills else self._bills
        for bill in self._bills:
            bill_date = datetime.strptime(bill['summary']['due_date'], date_format).date().replace(day=1)
            if bill_date == year_month:
                return bill

    def get_investiment_yield(self, _datetime:datetime):
        if not self._investiment.get(_datetime):
            try:
                self._investiment[_datetime] = self.nu.get_account_investments_yield(_datetime)
            except Exception:
                self._investiment[_datetime] = 0.0
        return  self._investiment[_datetime]
    
    def get_transfers_date_range(self):
        self._bills = self.nu.get_bills() if not self._bills else self._bills
        if not self._bills:
            self._bills = self.nu.get_bills()
        last_date = datetime.strptime(self._bills[0]['summary']['due_date'], date_format).date()
        first_date = datetime.strptime(self._bills[-1]['summary']['due_date'], date_format).date().replace(day=1)
        return [ x.date() for x in date_range(first_date, last_date, freq='MS', inclusive='both')]


class B3fileIntegration:

    def __init__(self) -> None:
        self.file = read_excel('b3/posicao-2023-06-30-16-16-16.xlsx', sheet_name=None)
        self.sheets = self.file.keys()

    def get_totals(self):
        result = {}
        for index, value in self.file.items():
            result[index] = value.iloc[-1,-1]  # last line of last column
        return result
