--Crud

INSERT INTO final.books(isbn, book_title, category, rental_price, status,  author, publisher)
VALUES ('978-1-60129-456-2', 'TO KILL A MOCKING-BIRD', 'CLASSIC', 6.00, 'yes', 'Harper Lee', 
		'J.B Lippincott & Co.')

UPDATE final.members
SET member_address = '12 Main St'
where member_id = 'C101'

select 
issued_emp_id,
count(issued_id) total_books_issued
from final.issued_status
group by issued_emp_id
having count(issued_id) >2


select 
b.book_title,
b.isbn,
count(ist.issued_id) no_of_time_issued
INTO final.BOOK_ISSUE_COUNT
from final.books as b 
left join final.issued_status as ist
on ist.issued_book_isbn = b.isbn
group by b.book_title, b.isbn


select 
b.category,
sum(b.rental_price) total_rents,
count(*)
from final.books as b 
inner join final.issued_status as ist
on ist.issued_book_isbn = b.isbn
group by  b.category



--1. Books overdue 

select 
ist.issued_member_id,
m.member_name,
b.book_title,
ist.issued_date,
rts.return_date,
DATEDIFF(DAY, ist.issued_date, CAST(GETDATE() AS DATE)) AS overdue_days
from final.issued_status ist
inner join final.members m 
on m.member_id = ist.issued_member_id
inner join final.books b
on ist.issued_book_isbn = b.isbn
left join final.return_status rts
on rts.issued_id = ist.issued_id
where rts.return_date is NULL
	AND DATEDIFF(DAY, ist.issued_date, CAST(GETDATE() AS DATE)) > 30