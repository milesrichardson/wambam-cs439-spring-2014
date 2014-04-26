#its so cool it needs its own file

import random

#used when you've created a task
def get_cool_word():
    words = ["Sweet.", "Cool.", "Awesome.", "Dope.", "Word.", "Great.", "Wicked.", 
             "Solid.", "Super.", "Super-duper.", "Excellent.", "Nice.", "Chill."]
    index = random.randint(0, len(words) - 1)
    return words[index]
