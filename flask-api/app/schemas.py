from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2))
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6) and validate.Regexp("^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$", error="Password must contain at least one letter and one number."))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)

class UserOutSchema(Schema):
    id = fields.Int()
    email = fields.Email()
    name = fields.Str()
    created_at = fields.DateTime()
