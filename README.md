Command to start the web server:
source sqlalchemy-workspace/bin/activate && python site/site.py

You'll need to change the app.run() parameters at the bottom of site.py when
you run the site for real.

Layout (inside site/)
    - site.py has most control logic
    - models.py holds models for the two sql databases
    - database.py creates database sessions so they can be used in site.py
    - create\_db.py creates merged-associations.sql from gwas.out.sql. If
        merged-associations.sql exists, this doesn't need to be run
    - tmp holds the two sqlite databases
        - gwas.out.sql is the original database
        - merged-associations.sql takes relevant data from gwas.out.sql and
            puts it all in one table, for easy searching
    - templates holds the templates
    - static holds CSS. In particular, custom.css.
