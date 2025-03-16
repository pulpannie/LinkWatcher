def a(x):                                                                                                                
	for i in range(0,x):                                                                                                 
		if i == x-1:                                                                                                 
                	yield i                                                                                              
		else:                                                                                                        
			yield from a(x-1)


for i in a(4):
	print(i)
