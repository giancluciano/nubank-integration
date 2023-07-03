import cherrypy
from summaries import AccountSummaries, TotalSummary
from datetime import datetime
from pandas import DataFrame, options
from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("manage"),
    autoescape=select_autoescape()
)

class Main(object):
    def __init__(self) -> None:
        self.summaries = AccountSummaries()
        self.total_summary = TotalSummary()

    @cherrypy.expose
    def index(self):

        totals_table = self.total_summary.get_totals()
        
        totals = self.summaries.in_n_out_summary()
        index = [_date.strftime('%Y %b') for _date in self.summaries.nu_integration.get_transfers_date_range()][::-1]
        df = DataFrame.from_records(totals, index)
        template = env.get_template("index.html")
        return template.render(
            main_table=df.to_html(classes='ui table selectable compact right aligned collapsing green striped single line', escape=False),
            total_table=totals_table.to_html(classes='ui table selectable compact right aligned collapsing green striped', index=False)
            )


    @cherrypy.expose
    def detail(self, year_month):
        template = env.get_template("detail.html")
        year_month = datetime.strptime(year_month, '%Y-%m-%d').date()
        summary = self.summaries.money_movement_summary(year_month)
        money_in = DataFrame.from_records(summary['money-in']).to_html(classes='ui table selectable compact right aligned collapsing green striped single line')
        money_out = DataFrame.from_records(summary['money-out']).to_html(classes='ui table selectable compact right aligned collapsing green striped single line')
        return template.render(money_in=money_in, money_out=money_out)


if __name__ == '__main__':
    options.display.float_format = '${:,.2f}'.format
    #options.display.float_format = '$*****'.format
    cherrypy.quickstart(Main())