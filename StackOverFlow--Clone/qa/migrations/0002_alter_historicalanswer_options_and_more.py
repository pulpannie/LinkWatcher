# Generated by Django 4.2.11 on 2024-04-26 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historicalanswer",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical answer",
                "verbose_name_plural": "historical answers",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalbounty",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical bounty",
                "verbose_name_plural": "historical bountys",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalcommentq",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical comment q",
                "verbose_name_plural": "historical comment qs",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalqdownvote",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical q downvote",
                "verbose_name_plural": "historical q downvotes",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalquestion",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical question",
                "verbose_name_plural": "historical questions",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalqupvote",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical q upvote",
                "verbose_name_plural": "historical q upvotes",
            },
        ),
        migrations.AlterField(
            model_name="historicalanswer",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalbounty",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalcommentq",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalqdownvote",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalquestion",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalqupvote",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
    ]
