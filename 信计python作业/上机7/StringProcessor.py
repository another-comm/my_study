import string  

class StringProcessor:
    def __init__(self, text):
        self.text = text

    def reverse(self):

        return self.text[::-1]

    def count_substring(self, sub):

        return self.text.lower().count(sub.lower())

    def remove_punctuation(self):

        no_punct = ''.join(ch for ch in self.text if ch not in string.punctuation)
        return no_punct

sp = StringProcessor("Hello, World! Hello again...")

print("反转：", sp.reverse())  


print("出现次数：", sp.count_substring("hello"))  

print("去除标点：", sp.remove_punctuation())  
