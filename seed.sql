BEGIN;

-- 1) Здания
INSERT INTO buildings (id, address, latitude, longitude) VALUES
  (1, 'г. Москва, ул. Примерная, д. 1', 55.755800, 37.617300),
  (2, 'г. Санкт-Петербург, пр. Тестовый, д. 10', 59.934300, 30.335100),
  (3, 'г. Новосибирск, ул. Демо, д. 5', 55.008400, 82.935700)
ON CONFLICT (id) DO NOTHING;

-- 2) Виды деятельности (иерархия: родитель -> дети)
-- Корневые
INSERT INTO activities (id, name, parent_id) VALUES
  (1, 'Еда', NULL),
  (2, 'Услуги', NULL),
  (3, 'Спорт', NULL)
ON CONFLICT (id) DO NOTHING;

-- Дети для "Еда"
INSERT INTO activities (id, name, parent_id) VALUES
  (10, 'Кафе', 1),
  (11, 'Ресторан', 1),
  (12, 'Доставка еды', 1)
ON CONFLICT (id) DO NOTHING;

-- Дети для "Услуги"
INSERT INTO activities (id, name, parent_id) VALUES
  (20, 'Парикмахерская', 2),
  (21, 'Ремонт телефонов', 2),
  (22, 'Химчистка', 2)
ON CONFLICT (id) DO NOTHING;

-- Дети для "Спорт"
INSERT INTO activities (id, name, parent_id) VALUES
  (30, 'Фитнес-клуб', 3),
  (31, 'Йога-студия', 3)
ON CONFLICT (id) DO NOTHING;

-- 3) Организации (привязка к зданиям)
INSERT INTO organizations (id, name, building_id) VALUES
  (100, 'ООО "Кафе Тест"', 1),
  (101, 'ООО "Доставка Быстро"', 1),
  (102, 'ИП "Барбер Демо"', 2),
  (103, 'ООО "Сервис Мобайл"', 2),
  (104, 'ООО "Фитнес Пример"', 3)
ON CONFLICT (id) DO NOTHING;

-- 4) Телефоны организаций (10-11 цифр)
INSERT INTO organization_phones (organization_id, phone) VALUES
  (100, '9000000000'),
  (100, '90000000001'),
  (101, '9010000000'),
  (102, '9020000000'),
  (103, '9030000000'),
  (104, '9040000000')
ON CONFLICT DO NOTHING;

-- 5) Связи организация <-> деятельность (many-to-many)
INSERT INTO organization_activity (organization_id, activity_id) VALUES
  (100, 10), -- кафе
  (100, 12), -- доставка еды (доп. активность)
  (101, 12), -- доставка еды
  (102, 20), -- парикмахерская
  (103, 21), -- ремонт телефонов
  (104, 30), -- фитнес-клуб
  (104, 31)  -- йога-студия
ON CONFLICT ON CONSTRAINT uq_org_activity DO NOTHING;

COMMIT;