import sys;
'''
print(sys.version)
print("hello world")
i=int(1)
if 7 == 2:
    print("zer false")
elif i < 2:
    print("zer true")

fruits = ["apple", "banana", "cherry"]
x,y,z =fruits
print(x)

j=int(9)
print(j)

x1 = (float(input("what do u want ?")))
x2 = (float(input("what do u need rawr")))

x3 = round(x1 + x2)
print(x1,x2,x3)

height = (int(input("what is the height ?")))
weight = (int(input("what is the weight ?")))
bmi = height/weight
print(bmi)

# docs.python.org where all the official where all the cods are stored !!

#print(*objects,sep='',end='\n',file=stdout, flush=False) object seperation end file out etc basic python formatting

print("hello",end="??? oh damn this avoids the deafult next line" )
print ('world')

#STRING 

name = str(input("what is ur name??")).strip().title()
#name = name.strip()
#name = name.capitalize()
#name = name.title() #first letter of every word capital
first,last = name.split()
print(first)
print(f,hello, {last})
print(name)

'''
'''
#FLOAT
x = float(input("what is x ?"))
y = float(input("what is y ?"))
z = x + y /2
print(f"{z:.2f}")


'''
'''
#def DEFINE (def)

def hello(to = "world"):
    print("hello,", to,sep= '    ') #to deifnes that this ine of print comes under defintion hello

hello()
name = input("what is your name?")
hello(name)#using the def hello() to print hello
hello(123)
'''
'''
def main():
    name = input("what is your name?")
    hello(name)

def hello(to = "world"):
    print("hello,", to,sep= '    ')

main()
'''
'''
def main():
    x = int(input("what is x ?"))
    print("x square is ",square(x)) #square of x is the def down by using main i am bringing new defintion here sso sqquare(n) us square(x)
    y = int(input("what is y ?"))
    print("root of y is ",root(y))
def square(n):
    return n*n
def root(m):
    return m**(1/2)

main()

'''
def main():
    x = int(input("what is x?"))
    if even(x):
        print("is even")
    else:
        print("is odd")
def even(n):
    if n % 2 == 0:
        return True
    else:
        return False

main()


