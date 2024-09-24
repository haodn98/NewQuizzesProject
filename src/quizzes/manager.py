from typing import List, Dict

import pymongo
from bson import ObjectId
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field, conint
from pymongo.errors import PyMongoError


class QuizNotFound(Exception):
    pass


class MongoManager:

    @classmethod
    def id_to_string(cls, document):
        try:
            document["_id"] = str(document["_id"])
        except(KeyError, TypeError):
            pass
        return document

    @classmethod
    async def to_list(cls, cursor):
        res = []
        async for el in cursor:
            res.append(cls.id_to_string(el))
        return res

    @classmethod
    async def check_if_exist(cls, db, query):
        res = await db.count_documents(query)
        if not res:
            return False
        return True


class QuizManager(MongoManager):

    @classmethod
    async def get_quiz(cls, db, quiz_id):
        if ObjectId.is_valid(quiz_id):
            existing_quiz = await db.find_one(
                {
                    "_id": ObjectId(quiz_id)
                }
            )
            if not existing_quiz:
                raise QuizNotFound("Quiz not found")
            return cls.id_to_string(existing_quiz)
        raise ValueError("Invalid Quiz id")

    @classmethod
    async def get_quiz_no_answers(cls, db, quiz_id):
        if ObjectId.is_valid(quiz_id):
            existing_quiz = await db.find_one(
                {
                    "_id": ObjectId(quiz_id)
                },
                projection={"correct_answers": 0},
            )
            if not existing_quiz:
                raise QuizNotFound("Quiz not found")
            return cls.id_to_string(existing_quiz)
        raise ValueError("Invalid Quiz id")

    @classmethod
    async def create_quiz(cls, db, quiz_data):
        new_quiz_id = await db.insert_one(quiz_data)
        return await cls.get_quiz(db, new_quiz_id.inserted_id)

    @classmethod
    async def get_all_quizzes(cls, db):
        quizzes = db.find()
        return await cls.to_list(quizzes)

    @classmethod
    async def get_all_quizzes_paginated(cls,
                                        collection: AsyncIOMotorCollection,
                                        query: Dict,
                                        page: int,
                                        per_page: int
                                        ) -> Dict:
        # Calculate skips
        skips = per_page * (page - 1)

        # Fetch total count of documents
        total_count = await collection.count_documents(query)

        # Fetch paginated documents
        cursor = collection.find(query).sort("_id").skip(skips).limit(per_page)
        documents = await cursor.to_list(length=per_page)

        for document in documents:
            document = QuizManager.id_to_string(document)

        # Calculate total pages
        total_pages = (total_count + per_page - 1) // per_page

        return {
            "documents": documents,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_count": total_count
        }

    @classmethod
    async def update_quiz(cls, db, quiz_id, update_data):
        if ObjectId.is_valid(quiz_id):
            document = await db.find_one_and_update(
                {
                    "_id": ObjectId(quiz_id)
                },
                {
                    "$set": update_data
                },
                return_document=pymongo.ReturnDocument.AFTER
            )
            if not document:
                raise QuizNotFound
            return cls.id_to_string(document)
        raise ValueError("Invalid Quiz id")

    @classmethod
    async def delete_quiz(cls, db, quiz_id):
        if ObjectId.is_valid(quiz_id):
            existing_quiz = await db.find_one_and_delete({"_id": ObjectId(quiz_id)})
            if not existing_quiz:
                raise QuizNotFound("Quiz not found")
            return existing_quiz
        raise ValueError("Invalid Quiz id")

    #
    #     @classmethod
    #     def delete_quizzes_by_credential(cls, query, **kwargs):
    #         try:
    #             result = cls.db.delete_many(query, **kwargs)
    #             return result.deleted_count
    #         except PyMongoError:
    #             return None
    #
    @classmethod
    async def quiz_filter(cls, db, query, projection=None):
        cursor = db.find(query, projection)
        return await cls.to_list(cursor)
