'''a=input(print('enter the value of a' ))
b=input(print('enter the value of b'))
c=input(print('enter the value of c'))


if (a>b) and (a>c):
    largest=a
elif(b>a) and (b>c):
    largest=b
else:
    largest=c


print("the largest no is " , largest)'''



list1=[10,20,30]
list2=[40,50,60]
newlist=list1+list2

print("the appended list is  :" ,newlist)
newlis1=newlist.pop()

print("the removed portion is : " ,newlis1)
print(newlist)