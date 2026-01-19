'''
def main():
    x = str(input("What is the Answer to the Great Question of Life, the Univerese, and Everything?")).lower().strip()
    #print(x)
    if x == "42" or x == "forty-two" or x == "forty two":
        print("yes")
    else:
        print("no")
main()

'''

'''
class bank():
    x = str(input("Greeting: ")).strip()
    if x=="Hello" or x=="Hello, Newman":
        print("$0")
    elif x == "How you doing":
        print("$20")
    elif x == "What's happening":
        print("$100")


bank()
'''
''' #thise blocks is vastly false
class main():
    x = str(input("whaat?"))
    
    if len(x)>2:
        x,y = x.split(".")
    else:
        print("len < 1")
                  
'''
'''
def main():
    x= str(input("File name: ")).strip()

    z=x.split(".")
    if len(z)==1:
        #print("application.octet-stream")
        y="null"

    elif len(z)>1:
        y=z[-1]
    y=y.strip()
    #print(y)


    if y=="jpg" or y=="jpeg":
        print("image/jpeg")
    elif y=="gif" or y=="png":
        print("image/"+y)
    elif y=="pdf" or  y=="PDF":
        print("application/pdf")
    elif y=="zip":
        print("application/"+y)
    elif y=="txt":
        print("text/plain")
    else:
        print("application/octet-stream")
main()
'''