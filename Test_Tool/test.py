import matplotlib.pyplot as plt
import networkx as nx
from math import ceil
import cPickle as pickle

class Child(object):
    def __init__(self, name, age):

        super(Child, self).__init__()
        self.name = name
        self.age = age

    def say_name(self):
        print(self.name)

class Person(Child):
    def __init__(self, name, age, salary, child):
        super(Person, self).__init__(name, age)

        self.salary = salary
        self.child = child

    def say_salary(self):
        print(self.salary)

    def say_child_name(self):
        self.child.say_name()

if __name__ == '__main__':
    Tom = Child('Tom', 3)
    Mom = Person('Mary', 30, 3000, Tom)

    Tom.say_name()
    Mom.say_name()

    f = open('test.pkl', 'wb')
    pickle.dump(Mom, f)

    f.close()

    print('pickle check')
    f1 = open('test.pkl', 'rb')
    m = pickle.load(f1)
    m.say_name()
    m.say_salary()
    m.say_child_name()

