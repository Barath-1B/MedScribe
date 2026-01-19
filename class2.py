'''
def main():
    difficulty = input("hard or easy")
    player = input("multiplayer or single-player")
    count = input("number of players")

    if difficulty == "hard":
        if player == "multiplayer":
            print("multiplayer")
        elif player == "single-player":
            print("single-player")
        else :
            print("enter valid option")

    elif difficulty == "easy":
        if player == "multiplayer":
            print("multiplayer")
        elif player == "single-player":
            print("single-player")
        else :
            print("enter valid option")

    else:
        print("enter a proper difficulty")

    if count == 1 or count == 2:
        print("1 or 2")
    else:
        print("more than 2")
main()
'''


def main(): #instead of def main i used class main which fucked the code up and showed an error that is class related
    x = g_int("what is x?")
    print(f"x is {x}")


def g_int(prompt): #i used def int and it overshadowed the built in int() hence an error where i cant use built int appeared

    while True:
        try:
            x=int(input(prompt)) # another method --- returtn int(input("whats x ? ")) works as welll
        except ValueError:
            pass #dont print anything
            #print("wtf?")
        else:
           # break #super important to break out of loops or repeat
            return x # return both recalls and breaks the program      
    #return x

main()
            