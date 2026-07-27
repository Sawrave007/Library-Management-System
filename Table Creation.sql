


CREATE TABLE final.branch (
    branch_id      VARCHAR(10) PRIMARY KEY,
    manager_id     VARCHAR(10),
    branch_address VARCHAR(100),
    contact_no     VARCHAR(20)
);

CREATE TABLE final.employees (
    emp_id    VARCHAR(10) PRIMARY KEY,
    emp_name  VARCHAR(50),
    position  VARCHAR(50),
    salary    DECIMAL(10,2),
    branch_id VARCHAR(10)
);



CREATE TABLE final.books (
    isbn         VARCHAR(20) PRIMARY KEY,
    book_title   VARCHAR(100),
    category     VARCHAR(50),
    rental_price DECIMAL(10,2),
    status       VARCHAR(20),
    author       VARCHAR(100),
    publisher    VARCHAR(100)
);

CREATE TABLE final.members (
    member_id      VARCHAR(10) PRIMARY KEY,
    member_name    VARCHAR(50),
    member_address VARCHAR(100),
    reg_date       DATE
);

CREATE TABLE final.issued_status (
    issued_id        VARCHAR(10) PRIMARY KEY,
    issued_member_id VARCHAR(10),
    issued_book_name VARCHAR(100),
    issued_date      DATE,
    issued_book_isbn VARCHAR(20),
    issued_emp_id    VARCHAR(10)
);

CREATE TABLE final.return_status (
    return_id   VARCHAR(10) PRIMARY KEY,
    issued_id   VARCHAR(10),
    return_date DATE
);





--FK 

ALTER TABLE final.issued_status
ADD CONSTRAINT FK_issued_status_members
FOREIGN KEY (issued_member_id)
REFERENCES final.members(member_id);

ALTER TABLE final.issued_status
ADD CONSTRAINT FK_issued_status_books
FOREIGN KEY (issued_book_isbn)
REFERENCES final.books(isbn);


ALTER TABLE final.issued_status
ADD CONSTRAINT FK_issued_status_employees
FOREIGN KEY (issued_emp_id)
REFERENCES final.employees(emp_id);

ALTER TABLE final.return_status
ADD CONSTRAINT FK_return_status_issued
FOREIGN KEY (issued_id)
REFERENCES final.issued_status(issued_id);


ALTER TABLE final.employees
ADD CONSTRAINT FK_employees_branch
FOREIGN KEY (branch_id)
REFERENCES final.branch(branch_id);

