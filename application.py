from flask import Flask, request, jsonify
import pandas as pd
from sec_api import XbrlApi
from sec_edgar_downloader import Downloader
from sec_downloader.types import RequestedFilings

app = Flask(__name__)

API_KEY = "9cdd3722b1fe0ca3e4249d93711530f82771e62cf679e8dff1a5953acf8df5cf"
xbrlApi = XbrlApi(API_KEY)

@app.route('/income_statement', methods=['GET'])
def get_income_statement():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    dl = Downloader("anything", "dellacm@usi.ch")
    metadatas = dl.get_filing_metadatas(RequestedFilings(ticker_or_cik=ticker, form_type="10-K", limit=1))

    if not metadatas:
        return jsonify({"error": "No filings found for ticker"}), 404

    primary_doc_url = metadatas[0].primary_doc_url
    xbrl_json = xbrlApi.xbrl_to_json(htm_url=primary_doc_url)

    income_statement = process_income_statement(xbrl_json)
    return income_statement.to_json()

def process_income_statement(xbrl_json):
    income_statement_store = {}
    for usGaapItem in xbrl_json['StatementsOfIncome']:
        values = []
        indices = []
        for fact in xbrl_json['StatementsOfIncome'][usGaapItem]:
            if 'segment' not in fact:
                index = fact['period']['startDate'] + '-' + fact['period']['endDate']
                if index not in indices:
                    values.append(fact['value'])
                    indices.append(index)
        income_statement_store[usGaapItem] = pd.Series(values, index=indices)
    income_statement = pd.DataFrame(income_statement_store)
    return income_statement.T

if __name__ == '__main__':
    app.run(debug=True)

