import pyodbc,sys

timestamp='GETDATE()'

new_override_name_suffix = None

cursor=None
	
def setup_connect(database, server):
	global cursor
	cnxn = pyodbc.connect(r'Driver={SQL Server};Server='+server+';Database='+database+';Trusted_Connection=yes;')
	cursor = cnxn.cursor()

def get_override_id(**kawrs):
	'''
		pass shortname or longname or both, if both values are present then and condition will be used while quering the database
		required parameter is coaid for affect only one chart of account
	'''
	if 'coa_id' not in kawrs:
		raise ValueError('required parameters coa_id(int) is not passed')
	if  'shortname' not in kawrs and 'longname' not in kawrs:
		raise ValueError('one of the required parameters among shortname and longname is not passed')
	global cursor
	
	query = 'select PRGLMappingAccountId from PRGLMappingAccount where'
	shortname_cond = ' shortname=? and'
	longname_cond = ' longname=? and'
	coa_cond = ' PRGLOverrideMappingId=?'
	
	value = list()
	
	if 'shortname' in kawrs:
		query = query + shortname_cond
		value.append(kawrs['shortname'])
	if 'longname' in kawrs:
		query = query + longname_cond
		value.append(kawrs['longname'])
	if 'coa_id' in kawrs:
		query = query + coa_cond
		value.append(kawrs['coa_id'])
	
	query = query + ' order by LastModifiedTimestamp desc'
	cursor.execute(query,value)
	row=cursor.fetchone()
	new_override_id=None
	if row:
		new_override_id=row[0]
		return new_override_id
	else:
		print 'no override matching this criteria found'
		return None
		
def copy(source_coa_id=None,coa_id=None,override_id=None, unique=6):

	if source_coa_id is None or coa_id is None or override_id is None:
		raise ValueError('required values source_coa_id, coa_id and override_id not passed')
	if unique not in (6,7):
		raise ValueError('unique value must be name or description')
	
	unique = int(unique)
	#insert into PRGLmappingaccount (PRGLOverrideMappingId, IsAccrualFollowsCurrent, XrefCode, ClientId, LastModifiedUserId, LastModifiedTimestamp, ShortName, LongName, SortOrder) \
	new_override_name_suffix = '' if int(coa_id) != int(source_coa_id) else ' - copy'
	coa_id = str(coa_id)
	cursor.execute('select PRGLOverrideMappingId, IsAccrualFollowsCurrent, XrefCode, ClientId, LastModifiedUserId, LastModifiedTimestamp, ShortName, LongName, SortOrder from PRGLMappingAccount \
	where PRGLMappingAccountId=?', [override_id])
	
	insert_query='insert into PRGLMappingAccount(PRGLOverrideMappingId, IsAccrualFollowsCurrent, XrefCode, ClientId, LastModifiedUserId, LastModifiedTimestamp, ShortName, LongName, SortOrder) values\
	('+coa_id+',?,?,?,?,?,?,?,?)'
	
	row=cursor.fetchone()
	new_shortname=''
	#6 shortname 7 longname
	if row:
		row=list(row)
		new_shortname=row[unique] + new_override_name_suffix
		row[unique]=new_shortname
		row=row[1:]
		cursor.execute(insert_query,row)
		print 'inserted\n'+str(row)
	else:
		print 'no override with id',override_id
		return
	if unique == 6:
		new_override_id = get_override_id(shortname=new_shortname, coa_id=coa_id)
	elif unique == 7:
		new_override_id = get_override_id(longname=new_shortname, coa_id=coa_id)
	
	if not new_override_id: raise ValueError('unable to get primary key of newly created override')
	
	select_lineitems='select * from PRGLMappingAccountElementValue where PRGLmappingaccountID=?'
	cursor.execute(select_lineitems,[override_id])
	
	item=None
	insert_item_query='insert into PRGLMappingAccountElementValue (PRGLMappingAccountId, DFElementParamId, Value, ClientId, LastModifiedUserId, LastModifiedTimestamp) values '
	insert_item_query_2='(?,?,?,?,?,?),'
	insert_item_query_values=[]
	haveSome=False
	while True:
		row=cursor.fetchone()
		if not row:
			break;
		haveSome=True
		item=list(row[1:])
		item[0]=new_override_id		
		insert_item_query_values.append(item)
		insert_item_query += insert_item_query_2
		print item
	if haveSome:
		insert_item_query=insert_item_query[:-1] # remove etra comma at the end
		cursor.execute(insert_item_query,sum(insert_item_query_values,[]))
	
	#selecting criterias
	select_criteria='select * from PRGLCriteria where PRGLMappingAccountId=?'
	cursor.execute(select_criteria,[override_id])
	insert_item_query='insert into PRGLCriteria (PRGLCriteriaSourceId, PRGLCriteriaSourceObjectId, IsGrouping, PRGLCriteriaParameterId, PRGLMappingAccountId, PRGLCriteriaFilterId, Value, ClientId, LastModifiedUserId, LastModifiedTimestamp, PRGLCriteriaTokenObjectId)\
		values '
	insert_item_query_2='(?,?,?,?,?,?,?,?,?,?,?),'
	insert_item_query_values=[]
	haveSome=False
	while True:
		row=cursor.fetchone()
		if not row:
			break;
		haveSome=True
		item=list(row[1:])
		item[4]=new_override_id		
		insert_item_query_values.append(item)
		insert_item_query += insert_item_query_2
		print item
	if haveSome:
		insert_item_query=insert_item_query[:-1] # remove etra comma at the end
		cursor.execute(insert_item_query,sum(insert_item_query_values,[]))
	
	#inserting end overrides PRGLOverrideAssignment
	select_overrides=' select * from PRGLOverrideAssignment where PRGLMappingAccountId=?'
	cursor.execute(select_overrides,[override_id])
	insert_item_query='insert into PRGLOverrideAssignment (PRGLSegmentTypeId, PRGLSegmentTypeObjectId, PRGLMappingAccountId, PayrollDebitTypeId, PayrollDebitValue, PayrollCreditTypeId, PayrollCreditValue, AccrualTypeId, AccrualValue, AccrualOffsetTypeId, AccrualOffsetValue, ClientId, LastModifiedUserId, LastModifiedTimestamp)\
		values '
	insert_item_query_2='(?,?,?,?,?,?,?,?,?,?,?,?,?,?),'
	insert_item_query_values=[]
	haveSome=False
	while True:
		row=cursor.fetchone()
		if not row:
			break;
		haveSome=True
		item=list(row[1:])
		item[2]=new_override_id
		insert_item_query_values.append(item)
		insert_item_query += insert_item_query_2		
		print item
	if haveSome:
		insert_item_query=insert_item_query[:-1] # remove etra comma at the end
		cursor.execute(insert_item_query,sum(insert_item_query_values,[]))	
	#cursor.commit()

def commit(correct=True):
	global cursor
	if correct:
		cursor.commit()
	else:
		cursor.rollback()

	
	
def main():
	#select * from PRGLMappingAccount where PRGLOverrideMappingId=<coa ki id>	
	override_ids = [] # override ids to copy from source chart of account
	#select PRGLMappingOverrideId from PRGLMappingOverride
	destination_coa_ids = [12] # desctination CoA
	setup_connect('texanstmgtest', 'AN2NPVDFCSQL07.dforce1.navisite.net')
	
	for coa_id in destination_coa_ids:
		for override_id in override_ids:
			copy(source_coa_id=2,coa_id=coa_id, override_id=override_id)
		
if __name__=='__main__': main()