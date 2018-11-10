from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import re
from settings import APP_ROOT

# ----------------------------------------------------------------------------

# create sqlite database
engine = create_engine('sqlite:///{}/tmp/associations.sql'.format(APP_ROOT),
        convert_unicode=True)
engine2 = create_engine('sqlite:///{}/tmp/gwas-catalog.sql'.format(APP_ROOT),
        convert_unicode=True)

# create session to database
db1_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
db2_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine2))
Base = declarative_base()
Base2 = declarative_base()
Base.query = db1_session.query_property()
Base2.query = db2_session.query_property()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)
    #Base2.metadata.create_all(bind=engine)

    def make_auto_entry(line):
        tokens = re.split(r'\t+', line.decode('utf-8'))
        keywords = re.split(r'\|+', tokens[2])
        if (tokens[3] == '-'):
            tokens[3] = None
        entry = models.AutoAssociation(pmid=tokens[0], rsid=tokens[1],
                simple_phenotype=tokens[2], detailed_phenotype=tokens[3],
                pvalue=tokens[4])
        db1_session.add(entry)


    # data structure for automatically-curated database
    with open('{}/tmp/associations.tsv'.format(APP_ROOT)) as f:
        lines = f.readlines()
        for line in lines:
            make_auto_entry(line)
    db1_session.commit()
