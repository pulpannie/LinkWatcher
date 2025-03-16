import os
import json
import difflib

path = "/signup/"
x = []
y = []
full_path = os.getcwd() + path
for filename in os.listdir(full_path):
	with open(os.path.join(full_path, filename), 'r') as f:
		tmp_y = []
		json_obj = json.load(f)
		for key, item in json_obj.items():
			if key == 'request':
				x.append(item)
			else:
				tmp_y.append({key: item})
		y.append(tmp_y)
x_diff = []
for i, element in enumerate(x[:-1]):
	for j, element2 in enumerate(x[i+1:]):
		tmp_dict = {}
		for key, item in x[i].items():		
			x_diff.append({key:[li for li in difflib.ndiff(x[i][key], x[j][key]) if li[0] != ' ']})
print('input: ', x_diff)
y_diff = []
for i, element in enumerate(y[:-1]):
	for j, element2 in enumerate(y[i+1:]):
		for q, item in enumerate(element):
			item2 = element2[q]
			print("values:", item.values())
			for key, data in list(item.values())[0].items():
				for k, e in enumerate(data):
					print("key: ", key, data[k])
					y_1 = str(data[k])
					print("?", list(item2.values())[0][key])
					y_2 = str(list(item2.values())[0][key][k])
					y_diff.append({y_1 + ';' + y_2:[li for li in difflib.ndiff(y_1, y_2) if li[0] != ' ']})
print('output: ', y_diff)