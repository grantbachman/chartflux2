import unittest
import tasks

class TestTasks(unittest.TestCase):
    
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()
