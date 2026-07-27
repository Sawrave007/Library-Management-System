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
    TRY_CONVERT(DECIMAL(10,2), salary),
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
    TRY_CONVERT(DECIMAL(10,2), rental_price),
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
    TRY_CONVERT(DATE, reg_date)
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
    TRY_CONVERT(DATE, issued_date),
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
    TRY_CONVERT(DATE, r.return_date)
FROM raw.return_status r
INNER JOIN final.issued_status i
    ON r.issued_id = i.issued_id;

