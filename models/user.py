from main import Base, Column, Integer, String, LargeBinary

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    barcode_image = Column(LargeBinary)


class Reservation(Base):
    __tablename__ = 'reservation'
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer)
    amount_sits = Column(Integer)
    user_name = Column(String)
    tel_number = Column(String)
    hours = Column(String)