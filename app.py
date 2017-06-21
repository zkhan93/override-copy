from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape
from flask import request, redirect
import re
import find_db
import copy_override
import json
import pyodbc

app = Flask(__name__)

cursor=None


env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


@app.route('/')
def index():
	index_template = env.get_template('index.html')
	return index_template.render()

@app.route('/coa')
def get_coa():
	global cursor
	data=dict()
	data['server'] = request.args.get('server')
	data['database'] = request.args.get('database')
	cnxn = pyodbc.connect(r'Driver={SQL Server};Server='+data.get('server')+';Database='+data.get('database')+';Trusted_Connection=yes;')
	cursor = cnxn.cursor()
	cursor.execute('select PRGLOverrideMappingId, Shortname, Longname from PRGLOverrideMapping')
	coas=[]
	row = cursor.fetchone()
	while row:
		coas.append({'id':row[0],'name':row[1],'desc':row[2]})
		row = cursor.fetchone()
	data['coas'] = coas
	return json.dumps(data)

@app.route('/overrides')
def get_overrides():
	global cursor
	data=dict()
	data['coa_id'] = request.args.get('coa_id')
	cursor.execute('select PRGLMappingAccountId, shortname, longname from PRGLMappingAccount where PRGLOverrideMappingId='+data.get('coa_id','-1'))
	override=[]
	row=cursor.fetchone()
	while row:
		override.append({'id':row[0],'name':row[1],'desc':row[2]})
		row = cursor.fetchone()
	data['overrides']=override
	return json.dumps(data)
	
@app.route('/copy')
def copy():
	data = dict()
	data['server'] = request.args.get('server')
	data['database'] = request.args.get('database')
	data['source_coa'] = request.args.get('source_coa')
	data['destination_coas'] = parse_list(request.args.get('destination_coa'))
	data['override_ids'] = parse_list(request.args.get('override_ids'))
	data['unique'] = int(request.args.get('unique'))
	data['num_copy'] = int(request.args.get('num_copy',1))
	#data['server'] = find_db.get_server(data.get('database',None))
	
	print data
	copy_override.setup_connect(data.get('database'), data.get('server'))
	try:
		for coa_id in data.get('destination_coas'):
			for override_id in data.get('override_ids'):
				for n in range(data.get('num_copy')):
					copy_override.copy(source_coa_id = data.get('source_coa'),coa_id=coa_id, override_id=override_id, unique = data.get('unique'))
		data['status'] = True
	except Exception as e:
		data['error'] = str(e)
		data['status'] = False
	#index_template = env.get_template('index.html')
	return json.dumps(data)

@app.route('/commit')
def commit():
	data = dict()
	try:
		copy_override.commit(correct=True)
		data['status']=True
	except Exception as ex:
		data['status']=False
	return json.dumps(data)

@app.route('/cancel')
def cancel():
	data=dict()
	try:
		copy_override.commit(correct=False)
		data['status']=True
	except Exception as ex:
		data['status']=False
	return json.dumps(data)

@app.route('/search')
def search_server():
	data = dict()
	data['database'] = request.args.get('database','')
	if 'database' in data.keys(): 
		data['server'] = find_db.get_server(data.get('database',''))
	server_template = env.get_template('search_server.html')
	return server_template.render(data)

def parse_list(string):
	return filter(lambda x: x != '' , map(lambda x: str(x),re.split(',|, | ',string)))

if __name__=='__main__': app.run()
