from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import re
from settings import APP_ROOT

# ----------------------------------------------------------------------------

# create sqlite database
engine = create_engine('sqlite:////local_data/gwasdb/site/tmp/merged-associations.sql')
print APP_ROOT
print 'sqlite:///{}/tmp/merged-associations.sql'.format(APP_ROOT)
engine = create_engine('sqlite:///{}/tmp/merged-associations.sql'.format(APP_ROOT),
        convert_unicode=True)
engine2 = create_engine('sqlite:///{}/tmp/gwas.out.sql'.format(APP_ROOT),
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
    from models import MergedAssociation, Association, SNP, Phenotype, Paper
    Base.metadata.create_all(bind=engine)

    associations = db2_session.query(Association)
    i = 0
    for association in associations:
        if i % 1000 == 0:
            print(i)
        i += 1
        snp = db2_session.query(SNP) \
            .filter(SNP.id == association.snp_id).first()
        paper = db2_session.query(Paper) \
            .filter(Paper.id == association.paper_id).first()
        phenotype = db2_session.query(Phenotype) \
            .filter(Phenotype.id == association.phenotype_id).first()
        if association.source == 'gwasdb' and '\\' in phenotype.name:
            simple_phenotype = phenotype.name.split('\\')[0]
            detailed_phenotype = phenotype.name.split('\\')[2]
        else:
            simple_phenotype = phenotype.name
            detailed_phenotype = ''
        entry = MergedAssociation(
                pmid=paper.pubmed_id,
                rsid=snp.rs_id,
                simple_phenotype=simple_phenotype,
                detailed_phenotype=detailed_phenotype,
                pvalue=association.pvalue,
                authors=paper.authors,
                journal=paper.journal,
                title=paper.title,
                source=association.source,
                oddsratio=association.oddsratio,
                beta=association.beta,
                chrom=snp.chrom,
                position=snp.position,
                synonyms=phenotype.synonyms)
        db1_session.add(entry)

    db1_session.commit()
