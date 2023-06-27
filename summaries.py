from pynubank import Nubank
from datetime import datetime, date
import re
from pandas import DataFrame, date_range
from typing import List
from integrations import NubankIntegration

date_format = '%Y-%m-%d'


class AccountSummaries:
    def __init__(self) -> None:
        self.nu_integration = NubankIntegration()
        

    def _resume_transfer(self, transfer):
        resumed = {
            'postDate': transfer.date,
            'amount': transfer.amount
        }

        resumed['detail'] = re.sub('\\n.*', '', transfer.detail)

        return resumed

    def money_movement_summary(self, year_month):
        summary = {
            'money-in': [],
            'money-out': [],
            'internal': []
        }
        transfers = self.nu_integration.get_month_account_statements(year_month)
        for transfer in transfers:
            if 'money-in' in transfer.tag_list:
                summary['money-in'].append(self._resume_transfer(transfer))
            elif 'money-out' in transfer.tag_list:
                summary['money-out'].append(self._resume_transfer(transfer))
            else:
                summary['internal'].append(self._resume_transfer(transfer))
        return summary
    
    def _build_detail_button(self, year_month):
        return f'<button class="ui primary button" onclick="location.href=\'/detail?year_month={year_month}\'">Detalhe</button>'

    def in_n_out_month_summary(self, year_month:date):
        _datetime = datetime.combine(year_month, datetime.min.time())
        summary = {
            'Entrada': 0.0,
            'rendimento nuconta': self.nu_integration.get_investiment_yield(_datetime),
            'fatura': 0.0,
            'saida': 0.0,
            'lucro mensal': 0.0,
            'Detalhe': self._build_detail_button(year_month)
        }
        
        for transfer in self.nu_integration.get_month_account_statements(year_month):
            if 'money-in' in transfer.tag_list:
                summary['Entrada'] += transfer.amount
            elif 'money-out' in transfer.tag_list:
                summary['saida'] += transfer.amount
        summary['lucro mensal'] = summary['Entrada'] + summary['rendimento nuconta'] - summary['saida']

        bill = self.nu_integration.get_month_bill(year_month)
        summary['fatura'] = bill['summary']['total_balance'] / 100 if bill else 0.0
        if bill and bill['state'] in ['open', 'future']:
            summary['lucro mensal'] -= summary['fatura']
        return summary
    
    def in_n_out_summary(self):
        summary = []
        for year_month in self.nu_integration.get_transfers_date_range():
            summary.insert(0, self.in_n_out_month_summary(year_month))
        return summary
