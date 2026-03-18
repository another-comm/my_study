#类的继承和多态
#Student类
class Student():
    school = 'Jiangnan University'
    #构造方法：初始化实例对象
    def __init__(self,name,age,number,sex, **kw):
        self.name = name
        self.age = age
        self.number = number
        self.sex = sex
        super().__init__(**kw)
        
    #实例方法
    def sing(self,song):
        print(self.name + ' can sing' + song)

    def walk(self,step):
        print(self.name + ' can walk' + step)

    def math_score(self,score):
        self.score = score
        return self.score

    @classmethod
    def show(cls):
        return cls.school    
    
# 实例可以访问类中的所有方法
student1 = Student('May',20,7181500302,'female')
student1.sing(' 听妈妈的话')
print(student1.show())

#Teacher类
class Teacher():
    school = 'Jiangnan University'
    #构造方法：初始化实例对象
    def __init__(self,classroom,salary,**cw):
        self.classroom = classroom
        self.salary = salary
        super().__init__(**cw)
        
    def teach_course(self,course):
        self.course = course
        return self.course 

# 类的继承
#super(当前的类，当前的实例/类) —— 代理对象

class Student_new(Student,Teacher):
    def __init__(self,academy,**dw):
        super(Student_new,self).__init__(**dw)##自动分配参数
        self.academy = academy
    def sing(self,song,singer_name):
        super().sing(song)
        self.singer_name = singer_name
        print(self.name + ' can sing' + song + ' love singer' + singer_name)

    @classmethod
    def show(cls, adress):
        super(Student_new,cls).show()
        cls.adress = adress
        return cls.adress

student2 = Student_new(name='May',age=20,number=7181500302,\
                       sex='female',classroom='A103',salary='5k',academy='Science')
#子类调用父类中的实例方法
student2.walk(' 5000')
#子类继承父类实例方法改进后进行调用
student2.sing(' 听妈妈的话', ' 周杰伦')
#子类继承父类中的类方法改进并调用
student2.show('Wuxi Lihu street No.1800')
print(student2.show('Wuxi Lihu street No.1800'))
    
