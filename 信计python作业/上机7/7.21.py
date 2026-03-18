text = "I am a intelligent student. I think i can do it."
def alphi_I(a):
    words = a.split()
    for i in range(len(words)):
        if words[i] == 'i':
            words[i] = 'I'
    result = ' '.join(words)
    print(result)
alphi_I(text)    
