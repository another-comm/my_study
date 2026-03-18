# 类的继承和多态
# 定义父类
class Student():
    #构造方法
    school = 'Jiangnan University'
    def __init__(self, name, age, number, sex):
        self.name = name
        self.age = age
        self.number = number
        self.sex = sex

    #实例方法
    def sing(self, song):
        print(self.name + ' can sing' + song)

    def walk(self, step):
        print(self.name + ' can walk' + step)        

    #类方法
    @classmethod
    def show(cls):
        return cls.school
    
#实例化
student1 = Student('May', 20, 7151905003, 'female')
student1.sing(' 听妈妈的话')

#类的继承
#super(当前的类，当前的实例/类)
class Student_new(Student):
    def __init__(self, name, age, number, sex, academy):
        super(Student_new, self).__init__(name, age, number, sex)
        self.academy = academy

    def sing(self, song, singer_name):
        super().sing(song)
        self.singer_name = singer_name
        print(self.name + ' can sing' + song + ' love singer' + singer_name)
        
    @classmethod
    def show(cls, adress):
        super(Student_new, cls).show()
        cls.adress = adress
        return cls.adress

student2 = Student_new('May', 20, 7151905003, 'female', 'Science')
student2.walk(' 5000')
student2.sing(' 听妈妈的话', ' 周杰伦')
print(student2.show('Lihu Street No.1800'))
        
