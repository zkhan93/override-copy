servers=['to1npvdfcsql0{}.dforce1.navisite.net'.format(x) for x in range(5)]
servers.extend(['an2npvtstsql0{}.dforce1.navisite.net'.format(x) for x in range(5)])
def get_server(database):
	if database: return ''
	import pyodbc	
	found_on_server = None
	for server in servers:
		try:
			cnxn = pyodbc.connect(r'Driver={SQL Server};Server='+server+';Database='+database+';Trusted_Connection=yes;')
			cursor = cnxn.cursor()
			cursor.execute('select * from sys.tables')
			cursor.close()
			print ".",
		except Exception as e:
			pass
		else:
			found_on_server = server
			break;
	return server

def main():
	import sys
	database = str(sys.argv[1])
	print 'searching',str(sys.argv[1])
	print get_server(database)

if __name__=='__main__': main()