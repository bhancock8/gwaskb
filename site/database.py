from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import re
from settings import APP_ROOT
from math import log10, floor

# ----------------------------------------------------------------------------

# create sqlite database
# BJH 11/5/18: refactored all gwasdb -> gwaskb. Left this one unchanged to preserve path.
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


def import_gwaskb_associations():
    from models import MergedAssociation, Association, SNP, Phenotype, Paper
    Base.metadata.create_all(bind=engine)

    # read p-values directly from the tsv
    pvalues = {}
    with open('{}/tmp/associations.tsv'.format(APP_ROOT)) as f:
        lines = f.readlines()
        for line in lines:
            tokens = re.split(r'\t+', line.decode('utf-8'))
            # pvalues[(int(tokens[0]), tokens[1], tokens[2], tokens[3])] = 10 ** (float(tokens[4]))
            # keywords = re.split(r'\|+', tokens[2])
            if (tokens[3] == '-'):
                tokens[3] = None

            snp = db2_session.query(SNP) \
                .filter(SNP.rs_id == tokens[1]).first()
            paper = db2_session.query(Paper) \
                .filter(Paper.pubmed_id == int(tokens[0])).first()

            if tokens[3] is None:
                phenotype_name = tokens[2]
            else:
                phenotype_name = "\\\\".join([tokens[2], tokens[3]])
            phenotype_entry = Phenotype(name=phenotype_name, source="gwaskb")
            db2_session.add(phenotype_entry)
            db2_session.flush()

            # p_value = "Not found" if float(tokens[4]) < -999 else 10 ** (float(tokens[4]))
            p_value = 10 ** (float(tokens[4]))
            if p_value != 0:
                p_value = round(p_value, -int(floor(log10(abs(p_value)))))
            entry = Association(snp_id=snp.id, phenotype_id=phenotype_entry.id,
                    paper_id=paper.id, pvalue=p_value, source="gwaskb")
            db2_session.add(entry)

    db2_session.commit()


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
        if association.source == 'gwaskb' and '\\' in phenotype.name:
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
