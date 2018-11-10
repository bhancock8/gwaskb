from __future__ import print_function # In python 2.7
import os, time, sys
import os.path
from settings import APP_STATIC
from database import db1_session, db2_session

from models import AutoAssociation, SNP, Association, Paper, Phenotype

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

from accounts import create_app
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy


from flask import current_app

from sqlalchemy import *

import re


app = create_app()


@app.route('/')
def home():
    return render_template('home.html')


def find_results(query):
    results = db1_session.query(AutoAssociation) \
            .filter(or_(AutoAssociation.rsid == query, \
            AutoAssociation.simple_phenotype.like('%{}%'.format(query)), \
            AutoAssociation.detailed_phenotype.like('%{}%'.format(query))))
    return results


@app.route('/search')
def search():
    query = request.args.get('query')
    return render_template('search.html', query=query, results=find_results(query))


@app.route('/download')
def download():
    return render_template('download.html')


@app.route('/about')
def about():
    return render_template('about.html')



# Parses the 23andMe.txt file and stores the rsids identified in the file
# along with an rsid-genotype map for later use
def parse_23andMe(file):
    # 23andMe.txt file format:
    # tokens[0] = rsid, tokens[1] = chrom, tokens[2] = pos, tokens[3] = genotype
    lines = file.stream.readlines()

    rsids = []
    for line in lines:
        if line[0] == '#':
            continue

        rsid = line.split()[0]
        if rsid[:2] == 'rs':
            rsids.append(rsid)

    return rsids

def generate_gwas_catalog_results(user_rsids):
    user_rsids = user_rsids[:1000]  # FIXME
    result_map = {}
    for rsid in user_rsids:
        snp = db2_session.query(SNP).filter(SNP.rs_id == rsid).first()
        if snp:
            result_map[snp.id] = (rsid, [])
    associations = []
    for snp_id in result_map:
        associations = db2_session.query(Association) \
                .filter(Association.snp_id == snp_id)
        for association in associations:
            result_map[snp_id][1].append(association)

    results = result_map.values()
    complete_results = {}
    for result in results:
        rsid = result[0]
        complete_results[rsid] = []
        associations = result[1]
        for association in associations:
            paper = db2_session.query(Paper) \
                .filter(Paper.id == association.paper_id).first()
            phenotype = db2_session.query(Phenotype) \
                .filter(Phenotype.id == association.phenotype_id).first()
            complete_results[rsid].append([association, paper, phenotype])
    return complete_results

    
def generate_auto_results(rsids):
    all_results = []
    for rsid in rsids:
        results = db1_session.query(AutoAssociation) \
                .filter(AutoAssociation.rsid == rsid)
        for result in results:
            all_results.append(result)
        if len(all_results) > 100:  # FIXME
            return all_results
    return all_results

def generate_report(file):
    rsids = parse_23andMe(file)

    gwascatalog_results = generate_gwas_catalog_results(rsids)
    auto_results = generate_auto_results(rsids)

    generated_report = render_template('batch.html', auto_results=auto_results,
            gwascatalog_results=gwascatalog_results)
    return generated_report


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] == 'txt'

# Route that will process the file upload
@app.route('/batch', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('batch.html')
    else:
        # Get the name of the uploaded file
        file = request.files['file']
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            return generate_report(file)
        else:
            return render_template('batch.html', error=True)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db1_session.remove()
    db2_session.remove()

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(
        host='0.0.0.0',
        debug=True
    )
