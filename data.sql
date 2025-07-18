
-- Initial admin user and employee
INSERT INTO user (username, password_hash, role, email, _is_active) 
VALUES ('admin', 'pbkdf2:sha256:600000$dK0v7lGJ$acd86d0b10d2e7d49fd6c11b99b6d1c1d2b7d8e3f4a5b6c7d8e9f0a1b2c3d4e5', 'admin', 'admin@unbug.com', 1);

-- Initial clients
INSERT INTO client (name, email, phone, active) 
VALUES 
('Cliente Exemplo 1', 'cliente1@example.com', '(11) 99999-9999', 1),
('Cliente Exemplo 2', 'cliente2@example.com', '(11) 88888-8888', 1);

-- Initial suppliers
INSERT INTO supplier (name, email, phone, active)
VALUES 
('Fornecedor 1', 'fornecedor1@example.com', '(11) 77777-7777', 1),
('Fornecedor 2', 'fornecedor2@example.com', '(11) 66666-6666', 1);

-- Initial inventory items
INSERT INTO inventory_item (name, description, quantity, minimum_stock, unit_price, supplier_id)
VALUES 
('Item 1', 'Descrição do Item 1', 10, 5, 100.00, 1),
('Item 2', 'Descrição do Item 2', 15, 8, 150.00, 2);
