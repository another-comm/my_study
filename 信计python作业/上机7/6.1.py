class Person:
    def __init__(self, name='', age=20, sex='man'):
        self.setName(name)
        self.setAge(age)
        self.setSex(sex)

    def setName(self, name):
        if not isinstance(name, str):
            raise Exception('name must be a string.')
        self.__name = name

    def setAge(self, age):
        if type(age) != int or age < 0:
            raise Exception('age must be an integer.')
        self.__age = age

    def setSex(self, sex):
        if sex not in ('man', 'woman'):
            raise Exception('sex must be "man" or "woman"')
        self.__sex = sex

    def show(self):
        print(self.__name, self.__age, self.__sex, sep='\n')


# ✅ 创建 Student 类（继承自 Person）
class Student(Person):
    def __init__(self, name='', age=18, sex='man', score=0.0, major='', college=''):
        super().__init__(name, age, sex)  # 初始化继承的属性
        self.setScore(score)
        self.setMajor(major)
        self.setCollege(college)

    def setScore(self, score):
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            raise Exception('score must be a number between 0 and 100.')
        self.__score = score

    def setMajor(self, major):
        if not isinstance(major, str):
            raise Exception('major must be a string.')
        self.__major = major

    def setCollege(self, college):
        if not isinstance(college, str):
            raise Exception('college must be a string.')
        self.__college = college

    def show(self):
        super().show()
        print(self.__score, self.__major, self.__college, sep='\n')


# ✅ 测试创建 Student 对象并显示信息

stu = Student('LinXin', 21, 'man', 99, 'Information and Computing Science', 'Math College')
stu.show()

