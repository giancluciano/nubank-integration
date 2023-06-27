from pony import orm
from datetime import datetime, date

db = orm.Database("sqlite", "db.sqlite", create_db=True)

date_format = '%Y-%m-%d'

class Transfer(db.Entity):
    id = orm.PrimaryKey(str)
    date = orm.Required(date)
    amount = orm.Required(float)
    detail = orm.Required(str)
    tags = orm.Required(str)  # save as ','.join(tags)

    @property
    def tag_list(self):
        return self.tags.split(',')
    
    @orm.db_session
    def get_or_create(transfer):
        existing_transfer = Transfer.get(id=transfer.get('id'))
        if existing_transfer:
            return existing_transfer, False
        transfer = Transfer(
            id = transfer['id'],
            date = datetime.strptime(transfer['postDate'], date_format).date(),
            amount = transfer['amount'],
            detail = transfer['detail'] if transfer['detail'] else "No detail",
            tags = ','.join(transfer['tags']) if transfer.get('tags') else 'None',
        )
        return transfer, True  # obj, created flag
        



db.generate_mapping(create_tables=True)