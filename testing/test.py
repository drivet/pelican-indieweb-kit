import mf2py
import mf2util
import pprint

source_url = r'https://brid.gy/comment/twitter/desmondrivet/1117876830478852096/1118148721034891264'
target_url = r'https://desmondrivet.com/2019/04/15/20190415154611'

parsed = mf2py.Parser(url=source_url).to_dict()
comment = mf2util.interpret_comment(parsed, source_url, [target_url])
general = mf2util.interpret(parsed, source_url)

pprint.pprint(parsed)
print('-----\n')
pprint.pprint(comment)
