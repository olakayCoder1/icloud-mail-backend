import uuid
from ..helpers.utils import db
from sqlalchemy.dialects.postgresql import UUID

class Account(db.Model):
    __tablename__ = 'accounts' 
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Use UUID as primary key
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<Account {self.email}>'

    @classmethod
    def add_account(cls, email, is_active=False):
        """Method to add a new account."""
        if Account.query.filter_by(email=email).first():
            return False  # Account already exists
        
        new_account = Account(email=email, is_active=is_active)
        db.session.add(new_account)
        db.session.commit()
        return new_account
    

    @classmethod
    def get_or_create(cls, email,is_active=None):
        """Get the configuration with the given title, or create it if it doesn't exist."""
        # Try to fetch the configuration with the given title
        account = cls.query.filter_by(email=email).first()

        # If no account is found, create a new one with default values
        if not account:
            account = cls(email=email,is_active=is_active if is_active else False)
            db.session.add(account)
            db.session.commit()
        
        return account

    @classmethod
    def get_account_count(cls):
        """Method to get the total count of accounts."""
        return cls.query.count()

    

class AccountConfig(db.Model):
    __tablename__ = 'account_configs'  # Table name, pluralized

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Use UUID as primary key
    title = db.Column(db.String(120), nullable=False, default="threshold")
    max_accounts = db.Column(db.Integer, nullable=False, default=10)  # Default value of 10

    def __repr__(self):
        return f'<AccountConfig {self.max_accounts}>'

    @classmethod
    def get_or_create(cls, title="threshold"):
        """Get the configuration with the given title, or create it if it doesn't exist."""
        # Try to fetch the configuration with the given title
        config = cls.query.filter_by(title=title).first()

        # If no configuration is found, create a new one with default values
        if not config:
            config = cls(title=title, max_accounts=10)  # default max_accounts = 10
            db.session.add(config)
            db.session.commit()
        
        return config