## Representation
Entities are captured in PostgreSQL tables with the following schema.

### Entities
The database includes the following entities:

#### Users
The `users` table includes:

* `id`, which specifies the unique ID for each user as an `INTEGER`. This column has the PRIMARY KEY constraint applied.
* `username`, which is the user’s chosen username as `TEXT`. A `UNIQUE` constraint ensures no two users can share the same username.
* `number`, which stores the user's contact number as `TEXT`.
* `password`, which stores the user's password as `TEXT`.
* `is_active`, a `BOOLEAN` indicating whether the user account is active.
* `avatar`, which stores the path or URL to the user's profile image as `TEXT`.
* `is_admin`, a `BOOLEAN` indicating if the user has admin privileges.
* `created_at` and `updated_at`, timestamps recording user creation and last update.

---

#### Items
The `items` table includes:

* `id`, the unique ID for each item as an `INTEGER`, with the PRIMARY KEY constraint applied.
* `owner_id`, the ID of the user who owns the item as an `INTEGER`, with a FOREIGN KEY constraint referencing `users.id`.
* `title`, the title of the item as `TEXT`.
* `description`, a detailed description of the item as `TEXT`.
* `image`, the path or URL to the item image as `TEXT`.
* `starting_bid`, the minimum bid for the item as `FLOAT`.
* `current_bid`, the latest bid amount as `FLOAT`.
* `is_active`, a `BOOLEAN` indicating if the item is still available for bidding.
* `winner_id`, the ID of the winning user as `INTEGER`, referencing `users.id`. This may be `NULL` until the auction ends.
* `created_at` and `end_at`, timestamps for item creation and auction end.

---

#### Bids
The `bids` table includes:

* `id`, the unique ID of each bid as an `INTEGER`, PRIMARY KEY.
* `item_id`, the ID of the item being bid on as `INTEGER`, with a FOREIGN KEY referencing `items.id`.
* `user_id`, the ID of the user placing the bid as `INTEGER`, with a FOREIGN KEY referencing `users.id`.
* `bid`, the bid amount as `FLOAT`.
* `created_at`, a `TIMESTAMP` recording when the bid was placed.

---

#### Comments
The `comments` table includes:

* `id`, the unique ID for each comment as `INTEGER`, PRIMARY KEY.
* `user_id`, the ID of the user who wrote the comment as `INTEGER`, referencing `users.id`.
* `item_id`, the ID of the item commented on as `INTEGER`, referencing `items.id`.
* `comment`, the comment text as `TEXT`.
* `created_at`, a `TIMESTAMP` recording when the comment was made.

---

#### Watchlists
The `watchlists` table includes:

* `user_id`, the ID of the user watching the item as `INTEGER`, referencing `users.id`.
* `item_id`, the ID of the item being watched as `INTEGER`, referencing `items.id`.

Together, `user_id` and `item_id` form a composite PRIMARY KEY, ensuring no duplicate watch entries.

---

#### Reports
The `reports` table includes:

* `id`, the unique ID of each report as `INTEGER`, PRIMARY KEY.
* `reporter_id`, the ID of the user submitting the report as `INTEGER`, referencing `users.id`.
* `target_id`, the ID of the reported item or user as `INTEGER`.
* `status`, an `ENUM` representing the report status (e.g., pending, resolved).
* `created_at`, a `TIMESTAMP` indicating when the report was submitted.

---

### Relationships

The below entity relationship diagram describes the relationships among the entities in the database.

![ER Diagram](erdiagram.png)

As detailed by the diagram:

* A user can add 0 to many items. Each item belongs to exactly one user (owner).  
* A user can place 0 to many bids, and each item can have 0 to many bids.  
* A user can write 0 to many comments, and each item can have 0 to many comments.  
* A user can watch 0 to many items, and each item can be watched by 0 to many users.  
* A user can submit 0 to many reports, and each item or user can be reported by 0 to many users.  
* Each bid, comment, watchlist entry, or report references the user who performed the action and the item it relates to.  
* The winner of an item (if auctioned) is linked to the user who placed the highest bid.
