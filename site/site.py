from __future__ import print_function # In python 2.7
import os, time, sys
import os.path
from settings import APP_STATIC
from database import db1_session, db2_session

from models import MergedAssociation

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

from accounts import create_app
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy


from flask import current_app

from sqlalchemy import *

import re
from collections import Counter


app = create_app()


@app.route('/')
def home():
    return render_template('home.html')


def find_results(query):
    results = db1_session.query(MergedAssociation) \
            .filter(or_(MergedAssociation.rsid == query, \
            MergedAssociation.simple_phenotype.like('%{}%'.format(query)), \
            MergedAssociation.detailed_phenotype.like('%{}%'.format(query)), \
            MergedAssociation.authors.like('%{}%'.format(query)), \
            MergedAssociation.title.like('%{}%'.format(query))
            ))
    for result in results:
        if '|' in result.simple_phenotype:
            phenotypes = result.simple_phenotype.split('|')
            result.simple_phenotype = next(p for p in phenotypes if query.lower() in p.lower())
    phenotypes = [(result.simple_phenotype, result.detailed_phenotype, \
            result.synonyms, result.source) for result in results]
    traits = Counter(phenotypes)
    return results, traits


@app.route('/search')
def search():
    query = request.args.get('query')
    results, traits = find_results(query)
    return render_template('search.html', query=query, results=results, traits=traits)


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

def generate_results(rsids):
    all_rsids_in_db = db1_session.query(MergedAssociation.rsid)
    all_rsids_in_db = [rsid[0] for rsid in all_rsids_in_db]
    rsids = [rsid for rsid in all_rsids_in_db if rsid in rsids]

    all_results = []
    for rsid in rsids:
        results = db1_session.query(MergedAssociation) \
                .filter(MergedAssociation.rsid == rsid)
        for result in results:
            all_results.append(result)
    phenotypes = [(result.simple_phenotype, result.detailed_phenotype, \
            result.synonyms, result.source) for result in all_results]
    traits = Counter(phenotypes)
    return all_results, traits

def generate_report(file):
    rsids = parse_23andMe(file)
    results, traits = generate_results(rsids)
    generated_report = render_template('batch.html', results=results, traits=traits)
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
    # TODO: change this
    app.run(
        host='0.0.0.0',
        debug=True
    )
