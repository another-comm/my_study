text = "I fInd It InterestIng to vIsIt chIna."
def alphI_i(a):
    words = a.split()
    for i in range(len(words)):
        word = words[i]
        if len(word) > 1:
            words[i] = word[0:].replace('I', 'i')
    result = ' '.join(words)
    print(result)
alphI_i(text)