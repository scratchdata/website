---
date: 2023-08-14
publishdate: 2023-08-14
title: Incremental Clickhouse Backups
summary: How to use Clickhouse's built-in backup functionality to backup and restore data to S3
tags: ["Engineering", "Clickhouse"]
---

Clickhouse comes with the ability to do incremental backup and restore to S3.
[The official docs are here](https://clickhouse.com/docs/en/operations/backup).
Here are some code snippets to make it work!

## How do I backup my Clickhouse data?

Backups are created with the `BACKUP TABLE` command. Create the first backup:

``` sql
-- Creates an initial base backup called "base_backup"
BACKUP TABLE your_table TO 
    S3('https://your-bucket.s3.amazonaws.com/backups/base_backup',
        'access_key_id', 'secret_key');
```

Then create an incremental backup, add the `base_backup` setting:

``` sql
-- Creates an incremental backup called "incremental_backup_1" on top of "base_backup"
BACKUP TABLE your_table TO 
    S3('https://your-bucket.s3.amazonaws.com/backups/incremental_backup_1',
        'access_key_id', 'secret_key')
SETTINGS
    base_backup = S3('https://your-bucket.s3.amazonaws.com/backups/base_backup',
        'access_key_id', 'secret_key');
```

You can create as many incremental backups as you'd like. Each incremental backup
can act as the base_backup for the next iteration. For example:


``` sql
-- Creates an n+1 incremental backup. Here, we create "incrementabl_backup_2"
-- on top of the last incremental backup (incremental_backup_1)
BACKUP TABLE your_table TO 
    S3('https://your-bucket.s3.amazonaws.com/backups/incremental_backup_2',
        'access_key_id', 'secret_key')
SETTINGS
    base_backup = S3('https://your-bucket.s3.amazonaws.com/backups/incremental_backup_1',
        'access_key_id', 'secret_key');
```

## How do I restore my Clickhouse backup?

You can restore data with the `RESTORE TABLE` command.
Choose the most recent backup and clickhouse 
traverse the chain of incrementals to repopulate the table. If there is a "break"
in the chain (one of the incremental backups is missing) then Clickhouse will throw an error.

Be aware that Clickhouse restores append to the target table, they do not *replace*
data. (Something I learned the hard way!)

``` sql
-- Clickhouse will restore data from incremental_backup_2, incremental_backup_1, and base_backup
-- This data will be appended to "your_table_restored" (data in that table will not be overwritten.)
RESTORE TABLE your_table as your_table_restored FROM 
S3('https://your-bucket.s3.amazonaws.com/backups/incremental_backup_2',
   'access_key_id', 'secret_key');
```

## How do I see the status of my backup or restore?

You can check the status of your backup or restore jobs. Every backup, restore, or error will display their status. This table
is emptied when Clickhouse restarts. The `status` column can have the following values:
CREATING_BACKUP, BACKUP_CREATED, BACKUP_FAILED, RESTORING, RESTORED, RESTORE_FAILED

``` sql
SELECT * FROM system.backups;
```

```
id:                e867e173-fac0-4a11-9e04-b944172f61a6
name:              S3('https://your-bucket.s3.amazonaws.com/backups/incremental_backup_2')
status:            BACKUP_CREATED
error:             
start_time:        2023-08-14 16:48:53
end_time:          2023-08-14 16:49:18
num_files:         229
total_size:        357502011
num_entries:       199
uncompressed_size: 356605495
compressed_size:   356605495
files_read:        0
bytes_read:        0
```

## Conclusion

Most of this is written in the Clickhouse docs themselves. It wasn't clear that incremental backups
could be taken "on top" of each other, whether restores append vs replace (they append),
and I did't know what would happen if there was a missing link
in the restore process. Hope this is helpful!

Finally, I'm building ScratchDB, which simplifies the sysadmin work needed to run Clickhouse 
in production. I'd love to hear from you!
