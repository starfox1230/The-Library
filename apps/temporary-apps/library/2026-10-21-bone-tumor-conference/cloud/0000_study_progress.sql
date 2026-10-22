CREATE TABLE `study_progress` (
	`user_id` text NOT NULL,
	`item_key` text NOT NULL,
	`field` text NOT NULL,
	`value` text NOT NULL,
	`updated` integer NOT NULL,
	PRIMARY KEY(`user_id`, `item_key`, `field`)
);
