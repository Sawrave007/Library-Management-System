-- ============================================================
-- RAW -> FINAL LOAD
-- TRY_CONVERT is used only where the destination column type
-- is NOT text (numeric, date, etc). Text-to-text columns are
-- passed through as-is.
-- ============================================================

-- ============================================================
-- DROP FKs (TRUNCATE is blocked on any table referenced by an
-- active FK constraint, regardless of truncate order or whether
-- the referencing table is empty)
-- ============================================================

ALTER TABLE final.issued_status DROP CONSTRAINT FK_issued_status_members;
ALTER TABLE final.issued_status DROP CONSTRAINT FK_issued_status_books;
ALTER TABLE final.issued_status DROP CONSTRAINT FK_issued_status_employees;
ALTER TABLE final.return_status DROP CONSTRAINT FK_return_status_issued;
ALTER TABLE final.employees DROP CONSTRAINT FK_employees_branch;


-- ============================================================
-- TRUNCATE (order no longer matters once FKs are dropped)
-- ============================================================

TRUNCATE TABLE final.return_status;
TRUNCATE TABLE final.issued_status;
TRUNCATE TABLE final.employees;
TRUNCATE TABLE final.books;
TRUNCATE TABLE final.members;
TRUNCATE TABLE final.branch;


INSERT INTO final.branch (
    branch_id,
    manager_id,
    branch_address,
    contact_no
)
SELECT
    branch_id,
    manager_id,
    branch_address,
    contact_no
FROM raw.branch;


INSERT INTO final.employees (
    emp_id,
    emp_name,
    position,
    salary,
    branch_id
)
SELECT
    emp_id,
    emp_name,
    position,
    TRY_CONVERT(DECIMAL(10,2), NULLIF(LTRIM(RTRIM(salary)), '')),
    branch_id
FROM raw.employees;


INSERT INTO final.books (
    isbn,
    book_title,
    category,
    rental_price,
    status,
    author,
    publisher
)
SELECT
    isbn,
    book_title,
    category,
    TRY_CONVERT(DECIMAL(10,2), NULLIF(LTRIM(RTRIM(rental_price)), '')),
    status,
    author,
    publisher
FROM raw.books;


INSERT INTO final.members (
    member_id,
    member_name,
    member_address,
    reg_date
)
SELECT
    member_id,
    member_name,
    member_address,
    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM(reg_date)), ''))
FROM raw.members;


INSERT INTO final.issued_status (
    issued_id,
    issued_member_id,
    issued_book_name,
    issued_date,
    issued_book_isbn,
    issued_emp_id
)
SELECT
    issued_id,
    issued_member_id,
    issued_book_name,
    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM(issued_date)), '')),
    issued_book_isbn,
    issued_emp_id
FROM raw.issued_status;


INSERT INTO final.return_status (
    return_id,
    issued_id,
    return_date
)
SELECT
    r.return_id,
    r.issued_id,
    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM(r.return_date)), ''))
FROM raw.return_status r
INNER JOIN final.issued_status i
    ON r.issued_id = i.issued_id;


-- ============================================================
-- RECREATE FKs
-- ============================================================

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


