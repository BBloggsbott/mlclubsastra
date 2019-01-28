create table if not exists members (
  regno integer primary key,
  name text not null,
  score integer not null default 0,
  password text not null,
  kaggle text not null
);
create table if not exists tasks (
    task text not null, 
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
create table if not exists submissions(
  regno integer not null,
  sublink text not null, 
  task text not null,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);