import { sqliteTable, text, integer, primaryKey } from 'drizzle-orm/sqlite-core';
export const studyProgress = sqliteTable('study_progress', {
  userId:text('user_id').notNull(),
  itemKey:text('item_key').notNull(),
  field:text('field').notNull(),
  value:text('value').notNull(),
  updated:integer('updated').notNull(),
}, table=>[primaryKey({columns:[table.userId,table.itemKey,table.field]})]);
