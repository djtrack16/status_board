import factory
from factory.declarations import Sequence, SubFactory, Iterator
from sqlmodel import Session
from app.models.monitor import Monitor
from app.models.monitor_check import MonitorCheck
from factory.faker import Faker


class MonitorFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = Monitor
    sqlalchemy_session: None
    sqlalchemy_session_persistence = "flush"

  id = Sequence(lambda n: n + 1)
  url = Faker("url")
  name = Faker("name")
  is_active = True

class MonitorCheckFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = MonitorCheck
    sqlalchemy_session = None
    sqlalchemy_session_persistence = "flush"

  monitor = MonitorFactory.build(name="name", url="url")
  status_code = Iterator([200, 404, 500])
  response_time_ms = Faker("pyfloat", positive=True, right_digits=3)
  success = Faker("boolean")
  checked_at = Faker("date_time_this_year")