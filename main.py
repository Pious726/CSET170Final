from flask import Flask, render_template, request, url_for, redirect
from sqlalchemy import create_engine, text
 
app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/bank"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()