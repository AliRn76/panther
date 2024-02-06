use std::collections::hash_map::Entry;
use std::collections::HashMap;
use std::collections::hash_map::Iter as HashMapIter;

#[derive(Clone, Debug)]
pub struct Tree<K, V> {
    pub value: V,
    subtrees: HashMap<K, Tree<K, V>>,
}

impl<K, V> Tree<K, V> {
    pub fn new(root_value: V) -> Self {
        Self {
            value: root_value,
            subtrees: HashMap::new(),
        }
    }

    pub fn iter(&self) -> TreeIter<'_, K, V> {
        TreeIter::new(self)
    }
}

impl<K, V> Tree<K, V>
    where
        K: Eq + core::hash::Hash,
{
    pub fn entry(&mut self, key: K) -> Entry<'_, K, Tree<K, V>> {
        self.subtrees.entry(key)
    }

    pub fn get<Q>(&self, key: &Q) -> Option<&Tree<K, V>>
        where
            K: core::borrow::Borrow<Q>,
            Q: ?Sized + Eq + core::hash::Hash,
    {
        self.subtrees.get(key)
    }

    pub fn get_mut<Q>(&mut self, key: &Q) -> Option<&mut Tree<K, V>>
        where
            K: core::borrow::Borrow<Q>,
            Q: ?Sized + Eq + core::hash::Hash,
    {
        self.subtrees.get_mut(key)
    }
}

impl<K, Q, V> core::ops::Index<&Q> for Tree<K, V>
    where
        K: Eq + core::hash::Hash + core::borrow::Borrow<Q>,
        Q: ?Sized + Eq + core::hash::Hash,
{
    type Output = Tree<K, V>;

    fn index(&self, key: &Q) -> &Tree<K, V> {
        self.subtrees.index(key)
    }
}

pub struct TreeIter<'a, K, V> {
    next_value: Option<(Vec<&'a K>, &'a V)>,
    tree_stack: Vec<HashMapIter<'a, K, Tree<K, V>>>,
    key_stack: Vec<&'a K>,
}

impl<'a, K, V> TreeIter<'a, K, V> {
    pub fn new(tree: &'a Tree<K, V>) -> Self {
        Self {
            next_value: Some((Vec::new(), &tree.value)),
            tree_stack: vec![tree.subtrees.iter()],
            key_stack: Vec::new(),
        }
    }
}

impl<'a, K, V> Iterator for TreeIter<'a, K, V> {
    type Item = (Vec<&'a K>, &'a V);

    fn next(&mut self) -> Option<Self::Item> {
        let mut result = None;
        core::mem::swap(&mut result, &mut self.next_value);

        loop {
            match self.tree_stack.last_mut() {
                Some(this_tree) => match this_tree.next() {
                    Some((k, child_tree)) => {
                        self.tree_stack.push(child_tree.subtrees.iter());
                        self.key_stack.push(k);

                        self.next_value = Some((self.key_stack.clone(), &child_tree.value));
                        break;
                    }
                    None => {
                        self.tree_stack.pop();
                        self.key_stack.pop();
                        continue;
                    }
                },
                None => {
                    self.tree_stack = Vec::new();
                    self.key_stack = Vec::new();
                    break;
                }
            }
        }

        result
    }
}
