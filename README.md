# RUSTIC PAGES


## OVERVIEW
Welcome to my website called 'RUSTIC PAGES'. It is a book review website that allows users to search for a book and share their reviews about it. They can also view reviews shared by other users. Let's create a wonderful community of avid book readers who love to read and share their insights with each other. Even if you're not an enthusiastic reader, you can always check out what others have to say about a book that has caught your attention while lying on a table or on a book shelf.


## VIDEO LINK
https://www.youtube.com/watch?v=PBNs7_mGhL8


## WEBSITE LAYOUT
Initially users are taken to a welcome page where they can either sign-up (new user) or login (existing user) using their credentials. During sign-up they've to fill in additional details that are mandatory. If either sign-up or login is unsuccessful, an error page is displayed detailing what went wrong and, if possible, includes a suggestion to help them.

Once successfully logged in, they are taken to their home page. Home page has a top bar that provides useful options to them. Towards the right of the top-bar, they've "user-related" section where they can delete their account or logout from current session. Towards the center is a search-bar that they can use to search for any book. It accepts either a book's title, its ISBN number or its author as input. If not sure, they can also provide only a part of their input. Search bar will list out all books that matched search criteria in a new page. From this page, they can select each book and they will be taken to its respective page.

Each book has a page that includes multiple sections.
1. First section: It includes details about the book such as author, ISBN, published year and two inputs: average score and review count, obtained directly from "Goodreads.com".
2. Second section: It includes current user's review for that book. If current user has already reviewed it, this section will show that review. Otherwise, user can add a new review by selecting a rating (1 to 5) and add a title and text to it.
3. Third section: It includes any reviews added by other users within the community. All reviews are listed in reverse chronological order from latest to earliest review.

Finally users can also access book information, pro-grammatically, using following REST API- **`/api/<isbn>`** where users can replace <isbn> with ISBN number of any book. This will return a JSON data including book details. If corresponding book information was not available or if ISBN number was not valid then a HTTP 404 error is returned.
